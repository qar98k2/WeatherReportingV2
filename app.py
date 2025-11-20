import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timezone
from streamlit_autorefresh import st_autorefresh

MONGO_URI = 'mongodb+srv://weatheruser:MyWeather2025@weather-cluster.nxxaooe.mongodb.net/weather_db?retryWrites=true&w=majority'
DB_NAME = 'weather_db'
COLLECTION_NAME = 'weather_data'

st.set_page_config(page_title="Weather Monitoring System", page_icon="Weather", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; color: white; }
    body, .stApp { background-color: #0f111a; }
    #MainMenu, footer, header {visibility: hidden;}
    h1 { font-weight: 800 !important; font-size: 3rem !important; color: #ffffff !important; }
    .stMetric { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border-radius: 20px; padding: 20px; border:1px solid rgba(255,255,255,0.2);}
    [data-testid="stMetricValue"] { color: #00ffc6 !important; font-size:2.5rem !important; font-weight:800 !important; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg,#ff6a00 0%,#ee0979 100%); }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_client():
    return MongoClient(MONGO_URI)
client = get_client()
db = client[DB_NAME]
col = db[COLLECTION_NAME]

# Helper
def parse_ts(ts):
    try: return pd.to_datetime(float(ts), unit='s')
    except: 
        try: return pd.to_datetime(ts, utc=True)
        except: return pd.NaT

# Data fetchers
def latest():
    doc = col.find({}).sort("timestamp", -1).limit(1)
    return list(doc)[0] if col.count_documents({}) > 0 else None

def recent(limit=100):
    data = col.find({}).sort("timestamp", -1).limit(limit)
    df = pd.DataFrame(list(data))
    if not df.empty and 'timestamp' in df.columns:
        df['timestamp'] = df['timestamp'].apply(parse_ts)
        df = df.dropna(subset=['timestamp']).sort_values('timestamp')
    return df

# Display functions
def display_header():
    col1, col2 = st.columns([3,1])
    with col1:
        st.markdown("# Weather Monitoring System")
        st.markdown("### Real-time • Quezon City, Philippines")
    with col2:
        if st.button("Export Data"):
            df = pd.DataFrame(list(col.find({}, {'_id':0})))
            csv = df.to_csv(index=False)
            st.download_button("Download CSV", csv, "weather_data.csv", "text/csv")

def display_live_view():
    st.markdown("## Live Streaming Dashboard")
    st.markdown("<div style='background: linear-gradient(135deg, rgba(0,255,198,0.1), rgba(0,255,198,0.2)); padding:15px; border-radius:15px; border:1px solid rgba(0,255,198,0.3);'><span style='color:#00ffc6; font-weight:600;'>Live • Auto-refresh every 15s</span></div>", unsafe_allow_html=True)
    
    latest_doc = latest()
    df = recent(100)
    
    if latest_doc:
        c1,c2,c3,c4 = st.columns(4)
        with c1: st.metric("Temperature", f"{latest_doc.get('temperature',0):.1f}°C")
        with c2: st.metric("Humidity", f"{latest_doc.get('humidity',0):.0f}%")
        with c3: st.metric("Pressure", f"{latest_doc.get('pressure',0):.0f} hPa")
        with c4: st.metric("Cloudiness", f"{latest_doc.get('cloudiness',0)}%")
        
        if not df.empty and 'temperature' in df.columns:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['temperature'], mode='lines+markers', line=dict(color='#ff6a00')))
            fig.update_layout(template="plotly_dark", height=400, title="Temperature Trend")
            st.plotly_chart(fig, use_container_width=True)

def display_historical_view():
    st.markdown("## Historical Data")
    df = pd.DataFrame(list(col.find({}, {'_id':0})))
    if df.empty:
        st.warning("No data yet")
        return
    if 'timestamp' in df.columns:
        df['timestamp'] = df['timestamp'].apply(parse_ts)
        df = df.dropna(subset=['timestamp']).sort_values('timestamp')
    st.metric("Total Records", len(df))
    st.dataframe(df.tail(50))
    if len(df)>1 and 'temperature' in df.columns:
        fig = px.line(df, x='timestamp', y='temperature', title="Temperature Over Time")
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

# Main app
def main():
    st_autorefresh(interval=15_000, key="refresh")
    display_header()
    tab1, tab2 = st.tabs(["Live Streaming", "Historical Data"])
    with tab1: display_live_view()
    with tab2: display_historical_view()

if __name__ == "__main__":
    main()
