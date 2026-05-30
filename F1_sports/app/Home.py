import streamlit as st
import pandas as pd
import sys
import fastf1
import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.scheduler.session_manager import SessionManager
from src.ingestion.telemetry import TelemetryIngestion
from src.ml.predictor import RacePredictor
from src.utils.notifications import NotificationManager

# Page Styling
st.set_page_config(
    page_title="F1 AI Pit Wall",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Look
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff1801;
    }
    .status-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #161b22;
        border: 1px solid #30363d;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar Branding
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/F1.svg/1200px-F1.svg.png", width=100)
st.sidebar.title("AI Pit Wall v1.0")
st.sidebar.markdown("---")

st.title("🏎️ F1 AI Race Intelligence")
st.markdown("Professional-grade telemetry analysis and strategic prediction platform.")

# --- PRODUCTION STATUS BOARD ---
st.subheader("🌐 Global System Status")
status_col1, status_col2, status_col3, status_col4 = st.columns(4)

with status_col1:
    st.metric("Scheduler", "🛰️ ACTIVE", help="Monitoring F1 API for live sessions")
with status_col2:
    st.metric("AI Core", "🧠 OLLAMA", delta="Gemma - 2B", delta_color="normal")

notifier = NotificationManager()
with status_col3:
    if notifier.is_enabled:
        st.metric("Telegram Bot", "📱 CONNECTED", delta="Push Alerts On")
    else:
        st.metric("Telegram Bot", "⚠️ DISCONNECTED", delta="Alerts Off", delta_color="inverse")

with status_col4:
    st.metric("ML Pipeline", "⚡ XGBOOST", help="Real-time predictive engine ready")

st.markdown("---")

# --- SMART RACE SELECTION ---
st.header("🏁 Historical Session Control")
st.markdown("Select a session to bootstrap the intelligence engine.")

col_y, col_r = st.columns(2)

with col_y:
    current_year = datetime.datetime.now().year
    selected_year = st.selectbox("Season", range(current_year, 2018, -1), index=1)

@st.cache_data
def get_race_list_and_default(year):
    try:
        schedule = fastf1.get_event_schedule(year)
        # Sort by round to find the latest completed event
        schedule = schedule[schedule['EventFormat'] != 'testing'].sort_values(by='RoundNumber')
        races = schedule['EventName'].tolist()
        
        # Find the latest race that has passed (or current)
        today = datetime.datetime.now()
        passed_races = schedule[schedule['EventDate'] <= today]
        default_idx = len(passed_races) - 1 if not passed_races.empty else 0
        
        return races, max(0, default_idx)
    except:
        return ["Bahrain Grand Prix", "Saudi Arabian Grand Prix", "Australian Grand Prix"], 0

race_list, default_race_idx = get_race_list_and_default(selected_year)

with col_r:
    selected_race = st.selectbox("Grand Prix Location", race_list, index=default_race_idx)

# --- BOOTSTRAP UI ---
if st.button(f"🚀 Bootstrap {selected_year} Intelligence Engine", use_container_width=True):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Placeholder for live training chart
    st.subheader("📊 Real-time Training Monitor")
    training_chart = st.empty()
    
    def update_ingestion_progress(current, total, message):
        percent = int((current / total) * 100)
        progress_bar.progress(percent)
        status_text.markdown(f"**{message}** ({percent}%)")

    def update_training_progress(iteration, total, history):
        percent = int((iteration / total) * 100)
        progress_bar.progress(percent)
        status_text.markdown(f"**AI Training Round {iteration}/{total}...**")
        
        # Update live chart
        hist_df = pd.DataFrame({
            'Training Loss': history['train'],
            'Validation Loss': history['test']
        })
        training_chart.line_chart(hist_df)

    with st.spinner(f"Establishing connection to F1 Data Lake..."):
        ingestion = TelemetryIngestion()
        path = ingestion.fetch_session_data(
            selected_year, 
            selected_race, 
            'R', 
            progress_callback=update_ingestion_progress
        )
        
        if path:
            predictor = RacePredictor()
            results = predictor.train_visual(str(path), progress_ui_callback=update_training_progress)
            
            if results:
                st.balloons()
                st.session_state['last_loaded_file'] = path.name
                
                st.markdown("---")
                st.header("📈 Strategy Engine Analytics")
                
                # Metrics Row
                m_col1, m_col2, m_col3 = st.columns(3)
                m_col1.metric("Final Model Precision (RMSE)", f"{results['history']['test'][-1]:.4f}s")
                m_col2.metric("Training Iterations", len(results['history']['train']))
                m_col3.metric("Dataset Size", f"{len(pd.read_parquet(path))} laps")

                # Final Features
                st.subheader("Strategic Feature Impact")
                imp_df = pd.DataFrame({
                    'Feature': list(results['importance'].keys()),
                    'Impact Score': list(results['importance'].values())
                }).sort_values(by='Impact Score', ascending=True)
                st.bar_chart(imp_df.set_index('Feature'))

                st.success("Intelligence Engine is fully synchronized and operational.")
        else:
            st.error("Failed to establish data connection. Check network and API availability.")
