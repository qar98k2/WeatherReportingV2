# File: /mnt/data/WeatherReportingV2-main/app.py
"""
Weather Monitoring Dashboard - Streamlit Cloud Optimized
Lightweight version that reads directly from MongoDB Atlas
No Kafka dependencies - just displays data from MongoDB

This version preserves your original structure and style while applying
targeted fixes for:
 - historical 0-24h queries (use UTC datetimes & robust fallback)
 - light-theme readability (CSS variables, explicit text color)
 - Excel export crash (sanitize data types and fallback to string export)
"""

import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
from streamlit_autorefresh import st_autorefresh
import logging
from io import BytesIO
import json
import numpy as np

# ==================== LOGGER (small robustness addition) ====================
logger = logging.getLogger("weather_dashboard")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

# ==================== CONFIGURATION ====================
# Try Streamlit secrets first (for cloud), fallback to environment variables (for local)
try:
    MONGO_URI = st.secrets["MONGO_URI"]
    DB_NAME = st.secrets.get("MONGO_DB_NAME", "weather_db")
    COLLECTION_NAME = st.secrets.get("MONGO_COLLECTION_NAME", "weather_data")
except Exception:
    import os
    MONGO_URI = os.getenv(
        "MONGO_URI",
        "mongodb+srv://weatheruser:MyWeather2025@weather-cluster.nxxaooe.mongodb.net/weather_db?retryWrites=true&w=majority"
    )
    DB_NAME = "weather_db"
    COLLECTION_NAME = "weather_data"

# Page config
st.set_page_config(
    page_title="Weather Monitoring System",
    page_icon="🌤️",
    layout="wide"
)

# ==================== MONGODB CONNECTION ====================
@st.cache_resource
def get_mongo_client():
    """Get MongoDB client with connection pooling"""
    try:
        client = MongoClient(MONGO_URI, maxPoolSize=10, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"❌ MongoDB Connection Error: {e}")
        st.stop()

client = get_mongo_client()
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# ==================== SIDEBAR ====================
st.sidebar.title("🌤️ Dashboard Controls")

cities = [
    "Quezon City",
    "Manila",
    "Cebu City",
    "Davao City",
    "Makati",
    "Tokyo",
    "Singapore",
    "Bangkok",
    "Seoul",
    "Los Angeles"
]

selected_city = st.sidebar.selectbox("📍 Select City", cities, index=0)

hours = st.sidebar.select_slider("⏰ Historical Range (hours)", options=[1, 6, 12, 24, 48, 72, 168], value=24)

theme = st.sidebar.radio("🎨 Theme", ["Dark", "Light"], horizontal=True)

auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (15s)", value=True)
if auto_refresh:
    st_autorefresh(interval=15000, key="refresh")

# ==================== STYLING ====================
# Use CSS variables so light theme doesn't render white text on white
if theme == "Dark":
    st.markdown("""
    <style>
        :root {
            --bg: #0f111a;
            --text: #ffffff;
            --muted: #9ca3af;
            --metric: #00ffc6;
        }
        body, .stApp, .block-container, .main, .reportview-container, .css-1d391kg {
            background-color: var(--bg) !important;
            color: var(--text) !important;
        }
        h1, h2, h3, .css-1v0mbdj, .css-18e3th9 { color: var(--text) !important; }
        [data-testid="stMetricValue"] { color: var(--metric) !important; font-size: 2rem !important; }
        .stDownloadButton button { color: var(--text) !important; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        :root {
            --bg: #f8f9fa;
            --text: #212529;
            --muted: #6c757d;
            --metric: #0d6efd;
        }
        body, .stApp, .block-container, .main, .reportview-container, .css-1d391kg {
            background-color: var(--bg) !important;
            color: var(--text) !important;
        }
        h1, h2, h3, .css-1v0mbdj, .css-18e3th9 { color: var(--text) !important; }
        [data-testid="stMetricValue"] { color: var(--metric) !important; font-size: 2rem !important; }
        .stDownloadButton button { color: var(--text) !important; }
    </style>
    """, unsafe_allow_html=True)

# ==================== DATA FUNCTIONS ====================
@st.cache_data(ttl=60)
def get_latest_data(city: str):
    """Fetch the most recent record for the selected city"""
    try:
        doc = collection.find_one(
            {"location": city},
            sort=[("timestamp", -1)]
        )
        # If timestamp is string, try to parse it so UI can display properly
        if doc and 'timestamp' in doc:
            try:
                doc['timestamp'] = pd.to_datetime(doc['timestamp'], utc=True)
            except Exception:
                # fallback: keep raw
                pass
        return doc
    except Exception as e:
        logger.exception(f"Error fetching latest data for {city}: {e}")
        return None


def get_historical_data(city: str, hours: int = 24):
    """Fetch historical data for the selected city within the last N hours"""
    try:
        cutoff_dt = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Try querying using datetime objects (recommended)
        cursor = collection.find({
            "location": city,
            "timestamp": {"$gte": cutoff_dt}
        }).sort("timestamp", 1)

        results = list(cursor)

        # If no results, fallback to ISO string matching (handles string-stored timestamps)
        if not results:
            cutoff_iso = cutoff_dt.isoformat()
            cursor = collection.find({
                "location": city,
                "timestamp": {"$gte": cutoff_iso}
            }).sort("timestamp", 1)
            results = list(cursor)

        df = pd.DataFrame(results)

        if not df.empty and 'timestamp' in df.columns:
            # Parse and coerce timestamps to timezone-aware UTC datetimes
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')

        return df

    except Exception as e:
        logger.exception(f"Error fetching historical data for {city}: {e}")
        return pd.DataFrame()


def parse_timestamp(ts):
    """Parse timestamp to timezone-aware datetime (robust)"""
    try:
        return pd.to_datetime(ts, utc=True, errors='coerce')
    except Exception:
        return pd.NaT

# ==================== HEADER ====================
st.title("🌤️ Weather Monitoring System")
st.markdown(f"**Real-time weather data from OpenWeatherMap API** | City: **{selected_city}**")
st.markdown("---")

# ==================== MAIN CONTENT ====================
tab1, tab2 = st.tabs(["📊 Live Dashboard", "📈 Historical Analysis"])

with tab1:
    st.header("Live Weather Data")

    # Live indicator
    st.markdown("""
    <div style='background: linear-gradient(135deg, rgba(0,255,198,0.06), rgba(0,255,198,0.12));
                padding: 15px; border-radius: 15px; border: 1px solid rgba(0,255,198,0.08); 
                margin-bottom: 20px; text-align: center;'>
        <span style='color: #00ffc6; font-weight: 600; font-size: 1.05rem;'>
            🔴 Live • Streaming Active • Auto-refresh every 15s
        </span>
    </div>
    """, unsafe_allow_html=True)

    latest = get_latest_data(selected_city)

    if latest:
        # Ensure timestamp is shown nicely
        ts_display = latest.get('timestamp')
        try:
            if pd.notna(ts_display):
                ts_str = pd.to_datetime(ts_display).strftime("%Y-%m-%d %H:%M:%S %Z")
            else:
                ts_str = str(latest.get('timestamp', 'N/A'))
        except Exception:
            ts_str = str(latest.get('timestamp', 'N/A'))

        # Main metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            temp = latest.get('temperature', 0) or 0
            feels = latest.get('feels_like', 0) or 0
            st.metric("🌡️ Temperature", f"{temp:.1f}°C", f"Feels like {feels:.1f}°C")

        with col2:
            st.metric("💧 Humidity", f"{latest.get('humidity', 0)}%")

        with col3:
            st.metric("💨 Wind Speed", f"{latest.get('wind_speed', 0):.1f} km/h")

        with col4:
            st.metric("☁️ Condition", latest.get('condition', 'N/A'))

        # Additional info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"🔍 Visibility: {latest.get('visibility', 0):.1f} km")
        with col2:
            st.info(f"🌫️ Pressure: {latest.get('pressure', 0)} hPa")
        with col3:
            st.info(f"☁️ Cloudiness: {latest.get('cloudiness', 0)}%")

        # Temperature alerts
        if temp >= 35:
            st.error("🔥 EXTREME HEAT WARNING! Temperature is dangerously high!")
        elif temp >= 32:
            st.warning("⚠️ Very hot weather. Stay hydrated!")
        elif temp <= 0:
            st.error("❄️ FREEZING! Temperature is at or below freezing point!")
        elif temp <= 10:
            st.warning("🥶 Cold weather. Dress warmly!")

        # Recent trend
        st.markdown("### 📈 Recent Trend (Last 100 readings)")
        recent_data = list(collection.find({"location": selected_city}, sort=[("timestamp", -1)], limit=100))
        if recent_data:
            df_recent = pd.DataFrame(recent_data)
            if 'timestamp' in df_recent.columns:
                df_recent['timestamp'] = pd.to_datetime(df_recent['timestamp'], utc=True, errors='coerce')
                df_recent = df_recent.dropna(subset=['timestamp'])
                df_recent = df_recent.sort_values('timestamp')

                # Plot
                fig = px.line(df_recent, x='timestamp', y='temperature',
                              title='Temperature Trend',
                              labels={'temperature': 'Temperature (°C)', 'timestamp': 'Time'})

                # Respect theme for color
                fig.update_traces(line_color='#ff6b6b', line_width=2)
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white' if theme == "Dark" else 'black')
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No timestamp field available in recent records to plot trend.")

        st.caption(f"Last updated: {ts_str}")
    else:
        st.warning(f"⚠️ No data available for {selected_city}")

with tab2:
    st.header(f"Historical Data - Last {hours} Hours")

    historical = get_historical_data(selected_city, hours)

    if not historical.empty:
        df = pd.DataFrame(historical)

        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
            df = df.dropna(subset=['timestamp'])
            df = df.sort_values('timestamp')
        else:
            st.warning("No timestamp field found in historical records.")
            df = pd.DataFrame()

        if df.empty:
            st.warning(f"⚠️ No historical data available for {selected_city}")
        else:
            # Stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total Records", len(df))
            with col2:
                st.metric("🌡️ Avg Temp", f"{df['temperature'].mean():.1f}°C")
            with col3:
                st.metric("💧 Avg Humidity", f"{df['humidity'].mean():.0f}%")
            with col4:
                st.metric("⏰ Time Range", f"{hours}h")

            # Hourly aggregation (works with 0-24h and irregular sampling)
            df['hour'] = df['timestamp'].dt.floor('H')
            agg = df.groupby('hour').agg({
                'temperature': ['mean', 'min', 'max'],
                'humidity': ['mean', 'min', 'max'],
                'pressure': 'mean'
            }).round(2).reset_index()

            # Flatten column names
            agg.columns = ['_'.join(col).strip('_') if isinstance(col, tuple) else col for col in agg.columns.values]

            # Normalize timestamp column name for plotting and export
            if 'hour' in agg.columns:
                agg = agg.rename(columns={'hour': 'timestamp'})
            elif agg.columns[0].startswith('hour'):
                agg = agg.rename(columns={agg.columns[0]: 'timestamp'})

            df_hourly = agg.copy()

            # Charts
            col1, col2 = st.columns(2)

            # Determine plot font color
            plot_font_color = 'white' if theme == "Dark" else 'black'

            with col1:
                fig_temp = go.Figure()
                fig_temp.add_trace(go.Scatter(
                    x=df_hourly['timestamp'],
                    y=df_hourly['temperature_mean'],
                    mode='lines',
                    name='Average',
                    line=dict(color='#ff6b6b', width=2)
                ))
                fig_temp.add_trace(go.Scatter(
                    x=df_hourly['timestamp'],
                    y=df_hourly['temperature_max'],
                    mode='lines',
                    name='Max',
                    line=dict(color='red', width=1, dash='dot')
                ))
                fig_temp.add_trace(go.Scatter(
                    x=df_hourly['timestamp'],
                    y=df_hourly['temperature_min'],
                    mode='lines',
                    name='Min',
                    line=dict(color='blue', width=1, dash='dot')
                ))
                fig_temp.update_layout(
                    title="Temperature Trend (Hourly)",
                    xaxis_title="Time",
                    yaxis_title="Temperature (°C)",
                    font=dict(color=plot_font_color),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_temp, use_container_width=True)

            with col2:
                fig_hum = go.Figure()
                fig_hum.add_trace(go.Scatter(
                    x=df_hourly['timestamp'],
                    y=df_hourly['humidity_mean'],
                    mode='lines',
                    name='Humidity',
                    line=dict(color='#4ecdc4', width=2),
                    fill='tozeroy'
                ))
                fig_hum.update_layout(
                    title="Humidity Trend (Hourly)",
                    xaxis_title="Time",
                    yaxis_title="Humidity (%)",
                    font=dict(color=plot_font_color),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_hum, use_container_width=True)

            # Simple forecast
            if len(df) > 10:
                from sklearn.linear_model import LinearRegression
                import numpy as np

                temp_df = df[['timestamp', 'temperature']].copy()
                temp_df['minutes'] = (temp_df['timestamp'] - temp_df['timestamp'].min()).dt.total_seconds() / 60
                X = temp_df[['minutes']].values
                y = temp_df['temperature'].values
                try:
                    model = LinearRegression().fit(X, y)
                    future = np.array([[X.max() + 60], [X.max() + 120], [X.max() + 180]])
                    pred = model.predict(future)

                    st.markdown("### 🔮 Temperature Forecast (Next 3 Hours)")
                    st.success(f"**+1 hour:** {pred[0]:.1f}°C | **+2 hours:** {pred[1]:.1f}°C | **+3 hours:** {pred[2]:.1f}°C")
                except Exception as e:
                    logger.exception(f"Forecasting error: {e}")

            # Export
            st.markdown("### 📥 Export Data")
            col1, col2 = st.columns(2)
            with col1:
                csv = df.to_csv(index=False)
                st.download_button("📄 Download CSV", csv, f"weather_{selected_city}.csv", "text/csv")
            with col2:
                # Robust Excel export: sanitize datatypes and fallback to string export if needed
                output = BytesIO()

                df_export = df.copy()
                df_hourly_export = df_hourly.copy()

                def _make_values_excel_safe(df_to_fix: pd.DataFrame) -> pd.DataFrame:
                    """
                    Convert tz-aware datetimes to naive, and convert any nested objects to JSON strings.
                    """
                    for col in df_to_fix.columns:
                        # 1) If column is datetime-like, make naive (remove tz)
                        if pd.api.types.is_datetime64_any_dtype(df_to_fix[col]):
                            try:
                                df_to_fix[col] = pd.to_datetime(df_to_fix[col], utc=True, errors='coerce')
                                # result is tz-aware (UTC); convert to naive for Excel
                                df_to_fix[col] = df_to_fix[col].dt.tz_localize(None)
                            except Exception:
                                # Ensure naive fallback
                                df_to_fix[col] = pd.to_datetime(df_to_fix[col], errors='coerce')
                        else:
                            # 2) For object dtype, ensure everything is string-serializable
                            if df_to_fix[col].dtype == 'O':
                                def _safe_val(v):
                                    if pd.isna(v):
                                        return v
                                    # dict / list / tuple => json string
                                    if isinstance(v, (dict, list, tuple)):
                                        try:
                                            return json.dumps(v, default=str, ensure_ascii=False)
                                        except Exception:
                                            return str(v)
                                    if isinstance(v, bytes):
                                        try:
                                            return v.decode('utf-8', errors='ignore')
                                        except Exception:
                                            return str(v)
                                    if isinstance(v, (np.ndarray,)):
                                        try:
                                            return json.dumps(v.tolist(), default=str, ensure_ascii=False)
                                        except Exception:
                                            return str(v)
                                    # pandas Timestamp with tzinfo
                                    try:
                                        tzinfo = getattr(v, 'tzinfo', None)
                                        if tzinfo is not None:
                                            try:
                                                return pd.to_datetime(v).tz_convert(None)
                                            except Exception:
                                                return pd.to_datetime(v).tz_localize(None)
                                    except Exception:
                                        pass
                                    # fallback
                                    return v

                                df_to_fix[col] = df_to_fix[col].apply(_safe_val)
                    return df_to_fix

                try:
                    df_export = _make_values_excel_safe(df_export)
                    df_hourly_export = _make_values_excel_safe(df_hourly_export)

                    # Extra guard: ensure datetime columns are naive
                    for c in df_export.select_dtypes(include=['datetime64[ns, tz]', 'datetime64[ns]']).columns:
                        try:
                            df_export[c] = pd.to_datetime(df_export[c], utc=True, errors='coerce').dt.tz_localize(None)
                        except Exception:
                            df_export[c] = pd.to_datetime(df_export[c], errors='coerce')

                    for c in df_hourly_export.select_dtypes(include=['datetime64[ns, tz]', 'datetime64[ns]']).columns:
                        try:
                            df_hourly_export[c] = pd.to_datetime(df_hourly_export[c], utc=True, errors='coerce').dt.tz_localize(None)
                        except Exception:
                            df_hourly_export[c] = pd.to_datetime(df_hourly_export[c], errors='coerce')

                    # Write to Excel
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_export.to_excel(writer, sheet_name='Raw Data', index=False)
                        df_hourly_export.to_excel(writer, sheet_name='Hourly Summary', index=False)

                except Exception as e:
                    # If something still fails, fallback to converting everything to strings and retry
                    logger.exception(f"Excel export failed (attempting string fallback): {e}")
                    try:
                        df_export_str = df_export.astype(str)
                        df_hourly_export_str = df_hourly_export.astype(str)
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_export_str.to_excel(writer, sheet_name='Raw Data', index=False)
                            df_hourly_export_str.to_excel(writer, sheet_name='Hourly Summary', index=False)
                    except Exception as e2:
                        # As a last resort, provide CSV export and a friendly error
                        logger.exception(f"Excel fallback also failed: {e2}")
                        st.error("Export failed: unable to write Excel file. You can still download CSV format.")
                        st.download_button("📄 Download CSV (raw)", df_export.to_csv(index=False), f"weather_{selected_city}.csv", "text/csv")
                    else:
                        st.download_button("📊 Download Excel", output.getvalue(),
                                           f"weather_{selected_city}.xlsx",
                                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                else:
                    # If primary path succeeded, provide the download button
                    st.download_button("📊 Download Excel", output.getvalue(),
                                       f"weather_{selected_city}.xlsx",
                                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.warning(f"⚠️ No historical data available for {selected_city}")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.sidebar.caption(f"Database: {DB_NAME}")
st.sidebar.caption("Pipeline: MongoDB-Kafka (Local)")
