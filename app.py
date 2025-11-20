"""
Weather Monitoring Dashboard
Streamlit-based dashboard for real-time and historical weather data visualization
"""

import streamlit as st
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timezone, timedelta
from streamlit_autorefresh import st_autorefresh
from io import BytesIO
from fpdf import FPDF
import numpy as np
from sklearn.linear_model import LinearRegression
from typing import Optional, Dict, Any, Tuple

from config import Config
from logger import setup_logger, log_error, log_success, log_warning
from constants import (
    FIELD_TIMESTAMP, FIELD_TEMPERATURE, FIELD_HUMIDITY,
    FIELD_PRESSURE, FIELD_LOCATION, FIELD_CONDITION,
    FIELD_DESCRIPTION, WEATHER_ICONS, WEATHER_DESCRIPTIONS,
    TEMP_DANGEROUS, TEMP_VERY_HOT, TEMP_HOT, TEMP_COLD, TEMP_FREEZING,
    ALERTS, COLOR_TEMPERATURE, COLOR_HUMIDITY, COLOR_PRESSURE,
    THEME_DARK_BG, THEME_DARK_TEXT, THEME_LIGHT_BG, THEME_LIGHT_TEXT
)

# Setup logger
logger = setup_logger(__name__)

# Page configuration
st.set_page_config(
    page_title=Config.DASHBOARD_TITLE,
    page_icon=Config.DASHBOARD_ICON,
    layout="wide"
)


# ==================== DATABASE CONNECTION ====================
@st.cache_resource
def get_mongo_client() -> Optional[MongoClient]:
    """
    Get MongoDB client with connection pooling
    
    Returns:
        MongoClient instance or None if connection fails
    """
    try:
        client = MongoClient(
            Config.MONGO_URI,
            maxPoolSize=Config.MONGO_MAX_POOL_SIZE,
            minPoolSize=Config.MONGO_MIN_POOL_SIZE,
            serverSelectionTimeoutMS=Config.MONGO_SERVER_SELECTION_TIMEOUT
        )
        # Test connection
        client.admin.command('ping')
        log_success(logger, "MongoDB connected for dashboard")
        return client
    except PyMongoError as e:
        log_error(logger, e, "Failed to connect to MongoDB")
        st.error("❌ Failed to connect to database. Please check your connection.")
        return None


# Initialize MongoDB connection
mongo_client = get_mongo_client()
if mongo_client:
    db = mongo_client[Config.MONGO_DB_NAME]
    collection = db[Config.MONGO_COLLECTION_NAME]
else:
    st.stop()


# ==================== HELPER FUNCTIONS ====================
def parse_timestamp(ts: Any) -> pd.Timestamp:
    """
    Parse timestamp from various formats
    
    Args:
        ts: Timestamp in various formats (float, string, datetime)
        
    Returns:
        Pandas Timestamp or NaT if parsing fails
    """
    try:
        # Try parsing as Unix timestamp
        return pd.to_datetime(float(ts), unit='s', utc=True)
    except (ValueError, TypeError):
        try:
            # Try parsing as ISO string
            return pd.to_datetime(ts, utc=True)
        except:
            return pd.NaT


def get_weather_icon(condition: str) -> str:
    """Get weather icon emoji for condition"""
    return WEATHER_ICONS.get(condition, "❓")


def get_weather_description(condition: str) -> str:
    """Get weather description for condition"""
    return WEATHER_DESCRIPTIONS.get(condition, "Unknown")


def get_temperature_alert(temp: float) -> Optional[str]:
    """
    Get temperature alert message based on thresholds
    
    Args:
        temp: Temperature in Celsius
        
    Returns:
        Alert message or None
    """
    if temp >= TEMP_DANGEROUS:
        return ALERTS["extreme_heat"]
    elif temp >= TEMP_VERY_HOT:
        return ALERTS["dangerous_heat"]
    elif temp >= TEMP_HOT:
        return ALERTS["very_hot"]
    elif temp <= TEMP_FREEZING:
        return ALERTS["freezing"]
    elif temp <= TEMP_COLD:
        return ALERTS["cold"]
    return None


# ==================== DATA FETCHING FUNCTIONS ====================
def fetch_latest_data(city: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch the most recent weather data
    
    Args:
        city: Optional city filter
        
    Returns:
        Latest weather data dictionary or None
    """
    try:
        query = {FIELD_LOCATION: city} if city else {}
        data = collection.find(query, {'_id': 0}).sort(FIELD_TIMESTAMP, -1).limit(1)
        data_list = list(data)
        return data_list[0] if data_list else None
    except PyMongoError as e:
        log_error(logger, e, "Error fetching latest data")
        return None


def fetch_recent_data(city: Optional[str] = None, limit: int = 100) -> pd.DataFrame:
    """
    Fetch recent weather data
    
    Args:
        city: Optional city filter
        limit: Maximum number of records to fetch
        
    Returns:
        DataFrame with recent weather data
    """
    try:
        query = {FIELD_LOCATION: city} if city else {}
        data = collection.find(query, {'_id': 0}).sort(FIELD_TIMESTAMP, -1).limit(limit)
        df = pd.DataFrame(list(data))
        
        if df.empty or FIELD_TIMESTAMP not in df.columns:
            return pd.DataFrame()
        
        # Parse timestamps
        df[FIELD_TIMESTAMP] = df[FIELD_TIMESTAMP].apply(parse_timestamp)
        df = df.dropna(subset=[FIELD_TIMESTAMP])
        df = df.set_index(FIELD_TIMESTAMP).sort_index()
        
        return df
    except PyMongoError as e:
        log_error(logger, e, "Error fetching recent data")
        return pd.DataFrame()


def fetch_historical_data(
    city: Optional[str] = None,
    hours: Optional[int] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fetch historical weather data with optional time range filter
    
    Args:
        city: Optional city filter
        hours: Optional hours to look back
        
    Returns:
        Tuple of (raw_df, aggregated_df)
    """
    try:
        query = {}
        
        # Add city filter
        if city:
            query[FIELD_LOCATION] = city
        
        # Add time range filter
        if hours:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            query[FIELD_TIMESTAMP] = {"$gte": cutoff_time.isoformat()}
        
        data = collection.find(query, {'_id': 0}).sort(FIELD_TIMESTAMP, -1)
        df = pd.DataFrame(list(data))
        
        if df.empty or FIELD_TIMESTAMP not in df.columns:
            return pd.DataFrame(), pd.DataFrame()
        
        # Parse timestamps
        df[FIELD_TIMESTAMP] = df[FIELD_TIMESTAMP].apply(parse_timestamp)
        df = df.dropna(subset=[FIELD_TIMESTAMP])
        df = df.set_index(FIELD_TIMESTAMP).sort_index()
        
        # Create hourly aggregation
        agg_df = df.resample('H').agg({
            FIELD_TEMPERATURE: ['mean', 'min', 'max'],
            FIELD_HUMIDITY: ['mean', 'min', 'max'],
            FIELD_PRESSURE: 'mean'
        }).round(2)
        
        # Flatten column names
        agg_df.columns = ['_'.join(col).strip() for col in agg_df.columns.values]
        agg_df = agg_df.reset_index()
        
        df = df.reset_index()
        return df, agg_df
        
    except PyMongoError as e:
        log_error(logger, e, "Error fetching historical data")
        return pd.DataFrame(), pd.DataFrame()


# ==================== UI STYLING ====================
def apply_theme_styling(theme: str):
    """Apply theme-specific CSS styling"""
    base_styles = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        * { font-family: 'Inter', sans-serif; }
        #MainMenu, footer, header {visibility: hidden;}
        h1 { font-weight: 800 !important; font-size: 3rem !important; }
        h2 { font-weight: 700 !important; font-size: 2rem !important; }
        h3 { font-weight: 600 !important; font-size: 1.5rem !important; }
        .stMetric { 
            background: rgba(255,255,255,0.05); 
            backdrop-filter: blur(10px); 
            border-radius: 20px; 
            padding: 20px; 
            border: 1px solid rgba(255,255,255,0.2);
        }
        [data-testid="stMetricValue"] { 
            font-size: 2.5rem !important; 
            font-weight: 800 !important; 
        }
    </style>
    """
    
    if theme == "Dark":
        dark_styles = f"""
        <style>
            body, .stApp {{ background-color: {THEME_DARK_BG}; color: {THEME_DARK_TEXT}; }}
            h1, h2, h3 {{ color: {THEME_DARK_TEXT} !important; }}
            [data-testid="stMetricValue"] {{ color: #00ffc6 !important; }}
        </style>
        """
        st.markdown(base_styles + dark_styles, unsafe_allow_html=True)
    else:
        light_styles = f"""
        <style>
            body, .stApp {{ background-color: {THEME_LIGHT_BG}; color: {THEME_LIGHT_TEXT}; }}
            h1, h2, h3 {{ color: {THEME_LIGHT_TEXT} !important; }}
            .stMetric {{ background: rgba(0,0,0,0.07); border: 1px solid rgba(0,0,0,0.2); }}
            [data-testid="stMetricValue"] {{ color: #0d6efd !important; }}
        </style>
        """
        st.markdown(base_styles + light_styles, unsafe_allow_html=True)


# ==================== DISPLAY FUNCTIONS ====================
def display_header(city: str):
    """Display dashboard header"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"# {Config.DASHBOARD_TITLE}")
        st.markdown(f"### Real-time • {city} • Philippines")
    with col2:
        if st.button("📥 Export Data", use_container_width=True):
            export_data(city)


def display_live_status():
    """Display live streaming status indicator"""
    st.markdown("""
    <div style='background: linear-gradient(135deg, rgba(0,255,198,0.1), rgba(0,255,198,0.2));
                padding: 15px; border-radius: 15px; border: 1px solid rgba(0,255,198,0.3); 
                margin-bottom: 20px; text-align: center;'>
        <span style='color: #00ffc6; font-weight: 600; font-size: 1.1rem;'>
            🔴 Live • Streaming Active • Auto-refresh every 15s
        </span>
    </div>
    """, unsafe_allow_html=True)


def display_weather_alerts(temp: float):
    """Display weather alerts based on temperature"""
    alert = get_temperature_alert(temp)
    if alert:
        if temp >= TEMP_VERY_HOT or temp <= TEMP_FREEZING:
            st.error(alert)
        else:
            st.warning(alert)


def display_live_metrics(latest: Dict[str, Any], theme: str):
    """Display live weather metrics"""
    # Weather condition
    condition = latest.get(FIELD_CONDITION, 'Unknown')
    desc = latest.get(FIELD_DESCRIPTION, '').title()
    icon = get_weather_icon(condition)
    description = get_weather_description(condition)
    
    st.markdown(f"### {icon} Current Weather: {description}")
    if desc:
        st.caption(desc)
    
    # Temperature alerts
    temp = latest.get(FIELD_TEMPERATURE, 0)
    display_weather_alerts(temp)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🌡️ Temperature", f"{temp:.1f}°C")
    
    with col2:
        humidity = latest.get(FIELD_HUMIDITY, 0)
        st.metric("💧 Humidity", f"{humidity}%")
    
    with col3:
        pressure = latest.get(FIELD_PRESSURE, 0)
        st.metric("🔽 Pressure", f"{pressure} hPa")
    
    with col4:
        ts = parse_timestamp(latest.get(FIELD_TIMESTAMP))
        if pd.notna(ts):
            diff = (datetime.now(timezone.utc) - ts).total_seconds()
            st.metric("⏱️ Last Update", f"{int(diff)}s ago")
        else:
            st.metric("⏱️ Last Update", "N/A")


def display_temperature_trend(df: pd.DataFrame, theme: str):
    """Display temperature trend chart"""
    if df.empty or FIELD_TEMPERATURE not in df.columns:
        st.warning("No data available for temperature trend")
        return
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df[FIELD_TEMPERATURE],
        mode='lines+markers',
        name='Temperature',
        line=dict(color=COLOR_TEMPERATURE, width=3),
        fill='tozeroy',
        fillcolor=f'rgba(255, 106, 0, 0.1)',
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title="Temperature Trend (Recent)",
        xaxis_title="Time",
        yaxis_title="Temperature (°C)",
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white' if theme == "Dark" else 'black'),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_live_view(city: str, theme: str):
    """Display live weather dashboard"""
    st.markdown("## 📊 Live Weather Dashboard")
    display_live_status()
    
    # Fetch data
    latest = fetch_latest_data(city)
    recent_df = fetch_recent_data(city, limit=Config.MAX_RECENT_RECORDS)
    
    if not latest:
        st.warning(f"⚠️ No data available for {city}")
        return
    
    # Display metrics
    display_live_metrics(latest, theme)
    
    # Display trend chart
    st.markdown("### 📈 Recent Trend")
    display_temperature_trend(recent_df, theme)


def display_historical_charts(hourly_df: pd.DataFrame, theme: str):
    """Display historical data charts"""
    if hourly_df.empty:
        st.warning("No historical data available")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Temperature chart
        fig_temp = go.Figure()
        
        if f'{FIELD_TEMPERATURE}_mean' in hourly_df.columns:
            fig_temp.add_trace(go.Scatter(
                x=hourly_df[FIELD_TIMESTAMP],
                y=hourly_df[f'{FIELD_TEMPERATURE}_mean'],
                mode='lines',
                name='Average',
                line=dict(color=COLOR_TEMPERATURE, width=2)
            ))
        
        if f'{FIELD_TEMPERATURE}_max' in hourly_df.columns:
            fig_temp.add_trace(go.Scatter(
                x=hourly_df[FIELD_TIMESTAMP],
                y=hourly_df[f'{FIELD_TEMPERATURE}_max'],
                mode='lines',
                name='Max',
                line=dict(color='red', width=1, dash='dot')
            ))
        
        if f'{FIELD_TEMPERATURE}_min' in hourly_df.columns:
            fig_temp.add_trace(go.Scatter(
                x=hourly_df[FIELD_TIMESTAMP],
                y=hourly_df[f'{FIELD_TEMPERATURE}_min'],
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
        # Humidity chart
        fig_hum = go.Figure()
        
        if f'{FIELD_HUMIDITY}_mean' in hourly_df.columns:
            fig_hum.add_trace(go.Scatter(
                x=hourly_df[FIELD_TIMESTAMP],
                y=hourly_df[f'{FIELD_HUMIDITY}_mean'],
                mode='lines',
                name='Average',
                line=dict(color=COLOR_HUMIDITY, width=2),
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


def display_forecast(raw_df: pd.DataFrame):
    """Display temperature forecast"""
    if len(raw_df) < 10 or FIELD_TEMPERATURE not in raw_df.columns:
        return
    
    try:
        temp_df = raw_df[[FIELD_TIMESTAMP, FIELD_TEMPERATURE]].copy()
        temp_df['minutes'] = (
            temp_df[FIELD_TIMESTAMP] - temp_df[FIELD_TIMESTAMP].min()
        ).dt.total_seconds() / 60
        
        X = temp_df[['minutes']].values
        y = temp_df[FIELD_TEMPERATURE].values
        
        model = LinearRegression().fit(X, y)
        
        # Predict next 3 hours
        future_minutes = np.array([[X.max() + 60], [X.max() + 120], [X.max() + 180]])
        predictions = model.predict(future_minutes)
        
        st.markdown("### 🔮 Temperature Forecast (Next 3 Hours)")
        st.success(
            f"**+1 hour:** {predictions[0]:.1f}°C | "
            f"**+2 hours:** {predictions[1]:.1f}°C | "
            f"**+3 hours:** {predictions[2]:.1f}°C"
        )
    except Exception as e:
        log_error(logger, e, "Error generating forecast")


def display_historical_view(city: str, hours: int, theme: str):
    """Display historical data and forecast"""
    st.markdown("## 📚 Historical Data & Forecast")
    
    # Fetch data
    raw_df, hourly_df = fetch_historical_data(city, hours)
    
    if raw_df.empty:
        st.warning(f"⚠️ No historical data available for {city}")
        return
    
    # Display stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Records", len(raw_df))
    with col2:
        if FIELD_TEMPERATURE in raw_df.columns:
            st.metric("🌡️ Avg Temp", f"{raw_df[FIELD_TEMPERATURE].mean():.1f}°C")
    with col3:
        if FIELD_HUMIDITY in raw_df.columns:
            st.metric("💧 Avg Humidity", f"{raw_df[FIELD_HUMIDITY].mean():.0f}%")
    with col4:
        st.metric("⏰ Time Range", f"{hours}h")
    
    # Display charts
    display_historical_charts(hourly_df, theme)
    
    # Display forecast
    display_forecast(raw_df)


def export_data(city: str):
    """Export weather data in multiple formats"""
    raw_df, hourly_df = fetch_historical_data(city)
    
    if raw_df.empty:
        st.error("❌ No data available to export")
        return
    
    st.markdown("### 📥 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    # CSV Export
    with col1:
        csv_data = raw_df.to_csv(index=False)
        st.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name=f"weather_{city}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # Excel Export
    with col2:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            raw_df.to_excel(writer, sheet_name='Raw Data', index=False)
            if not hourly_df.empty:
                hourly_df.to_excel(writer, sheet_name='Hourly Summary', index=False)
        excel_data = output.getvalue()
        
        st.download_button(
            label="📊 Download Excel",
            data=excel_data,
            file_name=f"weather_{city}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    # PDF Export
    with col3:
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, f"Weather Report - {city}", ln=1, align='C')
            pdf.set_font("Arial", size=12)
            pdf.ln(10)
            pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=1)
            pdf.cell(0, 10, f"Total Records: {len(raw_df)}", ln=1)
            
            if FIELD_TEMPERATURE in raw_df.columns:
                latest_temp = raw_df.iloc[-1][FIELD_TEMPERATURE]
                avg_temp = raw_df[FIELD_TEMPERATURE].mean()
                pdf.cell(0, 10, f"Latest Temperature: {latest_temp:.1f}°C", ln=1)
                pdf.cell(0, 10, f"Average Temperature: {avg_temp:.1f}°C", ln=1)
            
            pdf_output = pdf.output(dest='S').encode('latin1')
            
            st.download_button(
                label="📑 Download PDF",
                data=pdf_output,
                file_name=f"weather_{city}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            log_error(logger, e, "Error generating PDF")
            st.error("Failed to generate PDF")


# ==================== MAIN APPLICATION ====================
def main():
    """Main application entry point"""
    # Auto-refresh
    st_autorefresh(interval=Config.AUTO_REFRESH_INTERVAL, key="dashboard_refresh")
    
    # Sidebar controls
    st.sidebar.title("⚙️ Dashboard Controls")
    
    # City selection
    city = st.sidebar.selectbox(
        "📍 Select City",
        Config.SUPPORTED_CITIES,
        index=0
    )
    
    # Time range filter
    hours = st.sidebar.select_slider(
        "⏰ Historical Data Range (hours)",
        options=[1, 6, 12, 24, 48, 72, 168],
        value=24
    )
    
    # Theme toggle
    theme = st.sidebar.radio(
        "🎨 Theme",
        ["Dark", "Light"],
        horizontal=True
    )
    
    # Apply theme
    apply_theme_styling(theme)
    
    # Display header
    display_header(city)
    
    # Create tabs
    tab1, tab2 = st.tabs(["📊 Live Dashboard", "📚 History & Forecast"])
    
    with tab1:
        display_live_view(city, theme)
    
    with tab2:
        display_historical_view(city, hours, theme)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.sidebar.caption(f"Connected to: {Config.MONGO_DB_NAME}")


if __name__ == "__main__":
    main()
