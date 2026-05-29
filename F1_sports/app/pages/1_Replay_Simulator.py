import streamlit as st
import pandas as pd
import time
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.engine.replay_engine import ReplayEngine
from src.ml.prediction_tracker import PredictionTracker
from src.llm.ai_commentator import AICommentator
from src.config import RAW_DATA_DIR

st.set_page_config(page_title="Replay Simulator", page_icon="🏎️", layout="wide")

st.title("🏎️ Historical Race Simulator & Intelligence")

# Dynamic Data Loading
# Check if a specific file was just loaded in Home.py, otherwise default to the latest .parquet in raw data
import os

available_files = [f for f in os.listdir(RAW_DATA_DIR) if f.endswith('.parquet')]
if not available_files:
    st.warning("No historical data found. Please run the Bootstrap action on the Home page.")
    st.stop()

# Prioritize the last loaded file if it exists in session state
default_file = st.session_state.get('last_loaded_file', available_files[0])
if default_file not in available_files:
    default_file = available_files[0]

selected_file = st.sidebar.selectbox("Select Replay Data", available_files, index=available_files.index(default_file))
data_path = RAW_DATA_DIR / selected_file

# Initialize Engine & Trackers in Session State
# If the selected file changes, we MUST re-initialize the engine
if 'current_file' not in st.session_state or st.session_state.current_file != selected_file:
    st.session_state.engine = ReplayEngine(data_path)
    st.session_state.tracker = PredictionTracker()
    st.session_state.ai = AICommentator()
    st.session_state.is_playing = False
    st.session_state.playback_speed = 1.0
    st.session_state.commentary_log = []
    st.session_state.current_file = selected_file

engine = st.session_state.engine
tracker = st.session_state.tracker
ai = st.session_state.ai

# Sidebar Controls
st.sidebar.header("Replay Controls")

col_play, col_pause = st.sidebar.columns(2)
if col_play.button("▶️ Play"):
    st.session_state.is_playing = True
if col_pause.button("⏸️ Pause"):
    st.session_state.is_playing = False

st.session_state.playback_speed = st.sidebar.slider("Playback Speed (x)", 0.5, 5.0, 1.0, step=0.5)

# Jump to lap
jump_lap = st.sidebar.number_input("Jump to Lap", min_value=1, max_value=engine.max_laps, value=engine.current_lap)
if jump_lap != engine.current_lap and not st.session_state.is_playing:
    engine.set_lap(jump_lap)
    st.rerun()

st.sidebar.markdown(f"**Current Status:** {'🟢 PLAYING' if st.session_state.is_playing else '🔴 PAUSED'}")

# Main Execution Loop (Lap processing)
current_df = engine.get_current_state()

# 1. Evaluate previous predictions against current actuals
current_rmse = tracker.evaluate(engine.current_lap, current_df)

# 2. Predict next lap
tracker.predict_lap(engine.current_lap, current_df)

# --- UI RENDERING ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Current Lap", f"{engine.current_lap} / {engine.max_laps}")
col2.metric("Active Drivers", len(current_df['Driver'].unique()) if not current_df.empty else 0)
col3.metric("Prediction RMSE", f"{current_rmse:.3f}s", delta_color="inverse")
col4.metric("Engine Status", "Online")

st.markdown("---")

if not current_df.empty:
    # --- TRACK MAP SECTION ---
    if 'X' in current_df.columns and 'Y' in current_df.columns:
        st.subheader("📍 Live Track Position")
        # Use a scatter plot for the track map (X, Y coordinates)
        # We filter for unique driver positions to avoid cluttering if multiple points exist per lap
        map_data = current_df.groupby('Driver').first().reset_index()
        
        # Simple color mapping for teams (simplified for MVP)
        st.scatter_chart(
            map_data,
            x='X',
            y='Y',
            color='Driver',
            size=50,
            use_container_width=True
        )
        st.markdown("---")
    else:
        st.warning("⚠️ Spatial track data (X, Y) is not present in the current memory state. Please click **🔄 Reset Simulator** in the sidebar to load the newest data.")

    # Top Section: Telemetry & Predictions
    row1_col1, row1_col2 = st.columns([2, 1])
    
    with row1_col1:
        st.subheader("📊 Live Telemetry Stream")
        display_cols = ['Driver', 'LapTime', 'Compound', 'TyreLife', 'Position']
        # Add position safely if exists, else skip
        cols_to_show = [c for c in display_cols if c in current_df.columns]
        st.dataframe(current_df[cols_to_show].sort_values(by='LapTime').head(10), use_container_width=True, hide_index=True)

    with row1_col2:
        st.subheader("🎯 Prediction Accuracy")
        focal_driver = current_df.sort_values(by='LapTime').iloc[0]['Driver']
        driver_hist = tracker.history.get(focal_driver, {}).get(engine.current_lap, {})
        
        st.write(f"**Focal Driver:** {focal_driver}")
        st.metric("Predicted Time", f"{driver_hist.get('predicted', 0.0):.2f}s")
        st.metric("Actual Time", f"{driver_hist.get('actual', 0.0):.2f}s")
        st.metric("Model Confidence", f"{driver_hist.get('confidence', 0.0)*100:.1f}%")
        
        # Add visual history chart for the focal driver
        if focal_driver in tracker.history:
            hist_data = []
            for lap_num, data in tracker.history[focal_driver].items():
                if data.get('actual') is not None:
                    hist_data.append({
                        'Lap': lap_num,
                        'Predicted': data['predicted'],
                        'Actual': data['actual']
                    })
            if hist_data:
                hist_df = pd.DataFrame(hist_data).set_index('Lap')
                st.line_chart(hist_df)
        
    st.markdown("---")
    
    # Bottom Section: AI Commentary
    st.subheader("🎙️ Pit Wall AI Commentary")
    
    # Generate commentary every 3 laps or on manual pause to save LLM compute
    if engine.current_lap % 3 == 0 or not st.session_state.is_playing:
        focal_row = current_df.sort_values(by='LapTime').iloc[0]
        context = {
            'driver': focal_driver,
            'compound': focal_row.get('Compound', 'Unknown'),
            'tyre_life': focal_row.get('TyreLife', 0),
            'lap_time': focal_row.get('LapTime', 0.0),
            'predicted_next': driver_hist.get('predicted', 0.0),
            'confidence': driver_hist.get('confidence', 0.0)
        }
        with st.spinner("AI analyzing telemetry..."):
            msg = ai.generate_live_commentary(engine.current_lap, context, current_rmse)
            # Prepend to log
            st.session_state.commentary_log.insert(0, f"**Lap {engine.current_lap}:** {msg}")
            
    # Keep only last 5 messages
    st.session_state.commentary_log = st.session_state.commentary_log[:5]
    
    for log_msg in st.session_state.commentary_log:
        st.info(log_msg)

else:
    st.info("No data available for this lap.")

# Handle Playback Loop
if st.session_state.is_playing:
    if engine.current_lap < engine.max_laps:
        # Calculate sleep time based on speed (base = 2 seconds per lap for UI readability)
        sleep_time = 2.0 / st.session_state.playback_speed
        time.sleep(sleep_time)
        engine.next_lap()
        st.rerun()
    else:
        st.session_state.is_playing = False
        st.success("Replay Complete!")
        st.rerun()
