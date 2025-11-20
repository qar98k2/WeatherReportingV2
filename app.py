import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timezone
from streamlit_autorefresh import st_autorefresh
import os
from dotenv import load_dotenv
from io import BytesIO
from fpdf import FPDF
import numpy as np
from sklearn.linear_model import LinearRegression

load_dotenv()

# CONFIGURATION
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = 'weather_db'
COLLECTION_NAME = 'weather_data'

st.set_page_config(page_title="Weather Monitoring System", page_icon="🌤️", layout="wide")

# ==================== SIDEBAR CONTROLS ====================
st.sidebar.title("Dashboard Controls")

# City selection
city = st.sidebar.selectbox("City", ["Quezon City", "Manila", "Cebu City", "Davao City"], index=0)
st.session_state.selected_city = city

# Time range filter
hours = st.sidebar.select_slider("Historical Data Range (hours)", options=[1, 6, 12, 24, 48, 168], value=24)

# Theme toggle
theme = st.sidebar.radio("Theme", ["Dark", "Light"], horizontal=True)

# ==================== THEME STYLING ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    body, .stApp { background-color: #0f111a; color: white; }
    #MainMenu, footer, header {visibility: hidden;}
    h1 { font-weight: 800 !important; font-size: 3rem !important; color: #ffffff !important; }
    .stMetric { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border-radius: 20px; padding: 20px; border:1px solid rgba(255,255,255,0.2);}
    [data-testid="stMetricValue"] { color: #00ffc6 !important; font-size:2.5rem !important; font-weight:800 !important; }
</style>
""", unsafe_allow_html=True)

if theme == "Light":
    st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa; }
        h1, h2, h3 { color: #212529 !important; }
        .stMetric { background: rgba(0,0,0,0.07); border:1px solid rgba(0,0,0,0.2); }
        [data-testid="stMetricValue"] { color: #0d6efd !important; }
    </style>
    """, unsafe_allow_html=True)

# ==================== MONGO CONNECTION ====================
@st.cache_resource
def get_mongo_client():
    return MongoClient(MONGO_URI)
client = get_mongo_client()
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# ==================== DATA FUNCTIONS ====================
def parse_timestamp(ts):
    try:
        return pd.to_datetime(float(ts), unit='s')
    except:
        try:
            return pd.to_datetime(ts, utc=True)
        except:
            return pd.NaT

def fetch_latest_data():
    data = collection.find({}, {'_id': 0}).sort("timestamp", -1).limit(1)
    data_list = list(data)
    return data_list[0] if data_list else None

def fetch_recent_data(limit=100):
    data = collection.find({}, {'_id': 0}).sort("timestamp", -1).limit(limit)
    df = pd.DataFrame(list(data))
    if not df.empty and 'timestamp' in df.columns:
        df['timestamp'] = df['timestamp'].apply(parse_timestamp)
        df = df.dropna(subset=['timestamp'])
        df = df.set_index('timestamp').sort_index()
    return df

def fetch_all_data():
    data = collection.find({}, {'_id': 0}).sort("timestamp", -1)
    df = pd.DataFrame(list(data))
    if df.empty or 'timestamp' not in df.columns:
        return pd.DataFrame(), pd.DataFrame()
    
    df['timestamp'] = df['timestamp'].apply(parse_timestamp)
    df = df.dropna(subset=['timestamp'])
    df = df.set_index('timestamp').sort_index()

    # Hourly aggregation
    agg_df = df.resample('H').mean(numeric_only=True).round(2).reset_index()
    df = df.reset_index()
    return df, agg_df

# ==================== DISPLAY FUNCTIONS ====================
def display_header():
    col1, col2 = st.columns([3,1])
    with col1:
        st.markdown("# Weather Monitoring System")
        st.markdown(f"### Real-time • {city} • Philippines")
    with col2:
        if st.button("Export Data"):
            export_data()

def display_live_status():
    st.markdown("""
    <div style='background: linear-gradient(135deg, rgba(0,255,198,0.1), rgba(0,255,198,0.2));
                padding:15px; border-radius:15px; border:1px solid rgba(0,255,198,0.3); margin-bottom:20px;'>
        <span style='color:#00ffc6; font-weight:600; font-size:1.1rem;'>
            Live • Streaming Active • Auto-refresh every 15s
        </span>
    </div>
    """, unsafe_allow_html=True)

def display_live_view():
    st.markdown("## Live Weather Dashboard")
    display_live_status()
    
    latest = fetch_latest_data()
    recent_df = fetch_recent_data(limit=100)
    
    if latest:
        # Weather condition with icon
        condition = latest.get('condition', 'Unknown')
        desc = latest.get('description', '').title()
        icon_map = {
            "Clear": "Clear Sky",
            "Clouds": "Cloudy",
            "Rain": "Rainy",
            "Drizzle": "Drizzle",
            "Thunderstorm": "Thunderstorm",
            "Snow": "Snowy",
            "Mist": "Misty",
            "Fog": "Foggy",
            "Haze": "Hazy"
        }
        icon = icon_map.get(condition, "Unknown")
        st.markdown(f"### Current Weather: {icon} {desc}")

        # Alerts
        temp = latest.get('temperature', 0)
        if temp > 35:
            st.error("Dangerous Heat! Stay indoors.")
        elif temp > 32:
            st.warning("Very Hot! Stay hydrated.")
        elif temp < 10:
            st.error("Freezing Alert!")
        elif temp < 15:
            st.warning("Cold Alert!")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Temperature", f"{temp:.1f}°C")
        with col2:
            st.metric("Humidity", f"{latest.get('humidity', 0)}%")
        with col3:
            st.metric("Pressure", f"{latest.get('pressure', 0)} hPa")
        with col4:
            ts = parse_timestamp(latest.get('timestamp'))
            diff = (datetime.now(timezone.utc) - ts).total_seconds() if pd.notna(ts) else 0
            st.metric("Last Update", f"{int(diff)}s ago")

        # Trend chart
        if not recent_df.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=recent_df.index, y=recent_df['temperature'],
                                   mode='lines+markers', line=dict(color='#ff6a00', width=3),
                                   fill='tozeroy', fillcolor='rgba(255,106,0,0.1)'))
            fig.update_layout(height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                              font=dict(color='white' if theme == "Dark" else 'black'))
            st.plotly_chart(fig, use_container_width=True)

def display_historical_view():
    st.markdown("## Historical Data & Forecast")
    raw_df, hourly_df = fetch_all_data()
    
    if not raw_df.empty:
        st.metric("Total Records", len(raw_df))
        
        col1, col2 = st.columns(2)
        with col1:
            fig_temp = px.line(hourly_df, x='timestamp', y='temperature', title="Temperature Trend")
            fig_temp.update_layout(font=dict(color='white' if theme == "Dark" else 'black'))
            st.plotly_chart(fig_temp, use_container_width=True)
        with col2:
            fig_hum = px.line(hourly_df, x='timestamp', y='humidity', title="Humidity Trend")
            fig_hum.update_layout(font=dict(color='white' if theme == "Dark" else 'black'))
            st.plotly_chart(fig_hum, use_container_width=True)

        # Forecast
        if len(raw_df) > 10:
            temp_df = raw_df[['timestamp', 'temperature']].copy()
            temp_df['minutes'] = (temp_df['timestamp'] - temp_df['timestamp'].min()).dt.total_seconds() / 60
            X = temp_df[['minutes']].values
            y = temp_df['temperature'].values
            model = LinearRegression().fit(X, y)
            future = np.array([[X.max() + 60], [X.max() + 120], [X.max() + 180]])
            pred = model.predict(future)
            st.success(f"Next 3 Hours Forecast: {pred[0]:.1f}°C → {pred[1]:.1f}°C → {pred[2]:.1f}°C")

# ==================== EXPORT FUNCTION ====================
def export_data():
    raw_df, hourly_df = fetch_all_data()
    if raw_df.empty:
        st.error("No data to export")
        return
    
    # Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        raw_df.to_excel(writer, sheet_name='Raw Data', index=False)
        hourly_df.to_excel(writer, sheet_name='Hourly Summary', index=False)
    excel_data = output.getvalue()

    # PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Weather Report - Quezon City", ln=1, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=1)
    pdf.cell(0, 10, f"Latest Temperature: {raw_df.iloc[-1]['temperature']:.1f}°C", ln=1)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button("CSV", raw_df.to_csv(index=False), "weather.csv", "text/csv")
    with col2:
        st.download_button("Excel", excel_data, "weather_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with col3:
        pdf_output = pdf.output(dest='S').encode('latin1')
        st.download_button("PDF Report", pdf_output, "weather_report.pdf", "application/pdf")

# ==================== MAIN ====================
def main():
    st_autorefresh(interval=15_000, key="refresh")
    display_header()
    tab1, tab2 = st.tabs(["Live Dashboard", "History & Forecast"])
    with tab1:
        display_live_view()
    with tab2:
        display_historical_view()

if __name__ == "__main__":
    main()
