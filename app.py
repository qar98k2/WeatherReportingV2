"""
Weather Monitoring Dashboard - Streamlit Cloud Optimized
Lightweight version that reads directly from MongoDB Atlas
No Kafka dependencies - just displays data from MongoDB
"""

import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
from streamlit_autorefresh import st_autorefresh

# ==================== CONFIGURATION ====================
# Try Streamlit secrets first (for cloud), fallback to environment variables (for local)
try:
    MONGO_URI = st.secrets["MONGO_URI"]
    DB_NAME = st.secrets.get("MONGO_DB_NAME", "weather_db")
    COLLECTION_NAME = st.secrets.get("MONGO_COLLECTION_NAME", "weather_data")
except:
    import os
    MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://weatheruser:MyWeather2025@weather-cluster.nxxaooe.mongodb.net/weather_db?retryWrites=true&w=majority")
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
if theme == "Dark":
    st.markdown("""
    <style>
        .stApp { background-color: #0f111a; color: white; }
        h1, h2, h3 { color: #ffffff !important; }
        [data-testid="stMetricValue"] { color: #00ffc6 !important; font-size: 2rem !important; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa; color: #212529; }
        h1, h2, h3 { color: #212529 !important; }
        [data-testid="stMetricValue"] { color: #0d6efd !important; font-size: 2rem !important; }
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
        return doc
    except Exception as e:
        log_error(logger, e, "Error fetching latest data")
        return None


def get_historical_data(city: str, hours: int = 24):
    """Fetch historical data for the selected city within the last N hours"""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        cursor = collection.find({
            "location": city,
            "timestamp": {"$gte": cutoff.isoformat()}
        }).sort("timestamp", 1)

        df = pd.DataFrame(list(cursor))
        
        if not df.empty and 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
            
        return df
        
    except Exception as e:
        log_error(logger, e, "Error fetching historical data")
        return pd.DataFrame()
def parse_timestamp(ts):
    """Parse timestamp string to datetime"""
    try:
        return pd.to_datetime(ts)
    except:
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
    <div style='background: linear-gradient(135deg, rgba(0,255,198,0.1), rgba(0,255,198,0.2));
                padding: 15px; border-radius: 15px; border: 1px solid rgba(0,255,198,0.3); 
                margin-bottom: 20px; text-align: center;'>
        <span style='color: #00ffc6; font-weight: 600; font-size: 1.1rem;'>
            🔴 Live • Streaming Active • Auto-refresh every 15s
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    latest = get_latest_data(selected_city)
    
    if latest:
        # Main metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            temp = latest.get('temperature', 0)
            feels = latest.get('feels_like', 0)
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
            df_recent['timestamp'] = df_recent['timestamp'].apply(parse_timestamp)
            df_recent = df_recent.sort_values('timestamp')
            
            fig = px.line(df_recent, x='timestamp', y='temperature', 
                         title='Temperature Trend',
                         labels={'temperature': 'Temperature (°C)', 'timestamp': 'Time'})
            fig.update_traces(line_color='#ff6b6b', line_width=2)
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white' if theme == "Dark" else 'black')
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.caption(f"Last updated: {latest.get('timestamp', 'N/A')}")
    else:
        st.warning(f"⚠️ No data available for {selected_city}")

with tab2:
    st.header(f"Historical Data - Last {hours} Hours")
    
    historical = get_historical_data(selected_city, hours)
    
    if historical:
        df = pd.DataFrame(historical)
        df['timestamp'] = df['timestamp'].apply(parse_timestamp)
        df = df.sort_values('timestamp')
        
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
        
        # Hourly aggregation
        df_hourly = df.set_index('timestamp').resample('H').agg({
            'temperature': ['mean', 'min', 'max'],
            'humidity': ['mean', 'min', 'max'],
            'pressure': 'mean'
        }).round(2)
        df_hourly = df_hourly.reset_index()
        
        # Flatten column names for easier access
        df_hourly.columns = ['_'.join(col).strip('_') if isinstance(col, tuple) else col for col in df_hourly.columns.values]
        
        # Charts
        col1, col2 = st.columns(2)
        
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
                font=dict(color='white' if theme == "Dark" else 'black'),
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
                font=dict(color='white' if theme == "Dark" else 'black'),
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
            model = LinearRegression().fit(X, y)
            future = np.array([[X.max() + 60], [X.max() + 120], [X.max() + 180]])
            pred = model.predict(future)
            
            st.markdown("### 🔮 Temperature Forecast (Next 3 Hours)")
            st.success(f"**+1 hour:** {pred[0]:.1f}°C | **+2 hours:** {pred[1]:.1f}°C | **+3 hours:** {pred[2]:.1f}°C")
        
        # Export
        st.markdown("### 📥 Export Data")
        col1, col2 = st.columns(2)
        with col1:
            csv = df.to_csv(index=False)
            st.download_button("📄 Download CSV", csv, f"weather_{selected_city}.csv", "text/csv")
        with col2:
            from io import BytesIO
            output = BytesIO()
            
            # Remove timezone from datetime columns for Excel compatibility
            df_export = df.copy()
            if 'timestamp' in df_export.columns:
                df_export['timestamp'] = pd.to_datetime(df_export['timestamp']).dt.tz_localize(None)
            
            df_hourly_export = df_hourly.copy()
            if 'timestamp' in df_hourly_export.columns:
                df_hourly_export['timestamp'] = pd.to_datetime(df_hourly_export['timestamp']).dt.tz_localize(None)
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_export.to_excel(writer, sheet_name='Raw Data', index=False)
                df_hourly_export.to_excel(writer, sheet_name='Hourly Summary', index=False)
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
