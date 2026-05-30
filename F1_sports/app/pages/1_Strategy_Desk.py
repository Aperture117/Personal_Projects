import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.config import RAW_DATA_DIR
from src.ml.prediction_tracker import PredictionTracker
from src.engine.monte_carlo import MonteCarloSimulator
from src.llm.ai_commentator import AICommentator

st.set_page_config(page_title="F1 Strategy Deck", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    .metric-box { background-color: #161b22; padding: 20px; border-radius: 8px; border-left: 5px solid #ff1801; }
    .metric-value { font-size: 24px; font-weight: bold; color: white; }
    .metric-label { font-size: 12px; color: #8b949e; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 F1 Strategy Engineering Desk")
st.markdown("Advanced post-session analysis & probabilistic forecasting (Inspired by SBG RaceWatch).")

# --- DATA LOADING ---
available_files = [f for f in os.listdir(RAW_DATA_DIR) if f.endswith('_laps.parquet')]
if not available_files:
    st.warning("No data synchronized. Please go to **Home** and Bootstrap a session.")
    st.stop()

# Use the laps data directly since we aren't doing the sub-second map anymore
selected_file = st.sidebar.selectbox("Session Data", available_files)
data_path = RAW_DATA_DIR / selected_file

@st.cache_data
def load_data(path):
    df = pd.read_parquet(path)
    # Ensure valid lap times for analysis
    df = df[df['LapTime'] > 0]
    return df

df = load_data(data_path)
if df.empty:
    st.error("Loaded dataset is empty or invalid.")
    st.stop()
    
max_lap = int(df['LapNumber'].max())

# --- STRATEGY CONTROLS ---
st.sidebar.header("Strategy Context")
analysis_lap = st.sidebar.slider("Select Analysis Lap", 1, max_lap, min(15, max_lap))

# Get drivers who were active on the selected lap
current_lap_df = df[df['LapNumber'] == analysis_lap].copy()
if current_lap_df.empty:
    st.warning(f"No valid data recorded for Lap {analysis_lap}.")
    st.stop()
    
active_drivers = current_lap_df['Driver'].unique()
focal_driver = st.sidebar.selectbox("Focal Driver", active_drivers)

# Filter history up to the selected lap
history_df = df[df['LapNumber'] <= analysis_lap].copy()

# --- INITIALIZE ENGINES ---
# Initialize the Monte Carlo simulator (mocking the predictor dependency for now)
class MockPredictor: pass
mc_sim = MonteCarloSimulator(MockPredictor())
ai = AICommentator()

st.markdown("---")

# --- TOP ROW: KPI METRICS ---
focal_data = current_lap_df[current_lap_df['Driver'] == focal_driver].iloc[0]

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"<div class='metric-box'><div class='metric-label'>Target Driver</div><div class='metric-value'>{focal_driver}</div></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='metric-box'><div class='metric-label'>Pace (Lap {analysis_lap})</div><div class='metric-value'>{focal_data['LapTime']:.3f}s</div></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='metric-box'><div class='metric-label'>Tire Status</div><div class='metric-value'>{focal_data['Compound']} ({focal_data.get('TyreLife', 0)} Laps)</div></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='metric-box'><div class='metric-label'>Analysis Point</div><div class='metric-value'>L{analysis_lap} / L{max_lap}</div></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- MIDDLE ROW: DEEP ANALYTICS ---
row2_c1, row2_c2 = st.columns(2)

with row2_c1:
    st.subheader("📉 Pace & Degradation Curve")
    st.markdown("Analyzing lap time drop-off to predict the 'Tire Cliff'.")
    
    # Plot pace for top 3 drivers + focal driver based on current lap pace
    top_drivers = current_lap_df.sort_values('LapTime').head(3)['Driver'].tolist()
    if focal_driver not in top_drivers: 
        top_drivers.append(focal_driver)
    
    plot_df = history_df[history_df['Driver'].isin(top_drivers)]
    
    fig_pace = px.scatter(plot_df, x="LapNumber", y="LapTime", color="Driver", trendline="lowess", 
                          title="Lap Time History (Smoothed)")
    fig_pace.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#161b22', 
                           yaxis_title="Lap Time (s)", xaxis_title="Lap", height=400)
    st.plotly_chart(fig_pace, use_container_width=True)

with row2_c2:
    st.subheader("🎲 Monte Carlo Outlook")
    st.markdown("1,000 race simulations from this lap to determine optimal strategy.")
    
    remaining_laps = 57 - analysis_lap # Standard race distance proxy
    if remaining_laps > 0:
        with st.spinner("Running Monte Carlo simulations..."):
            probs = mc_sim.run_simulations(current_lap_df, remaining_laps)
        
        if probs:
            prob_df = pd.DataFrame([
                {'Driver': d, 'Win Probability': p['win_prob']*100, 'Podium Probability': p['podium_prob']*100} 
                for d, p in probs.items()
            ]).sort_values('Win Probability', ascending=False).head(6)
            
            fig_prob = px.bar(prob_df, x='Driver', y=['Win Probability', 'Podium Probability'], 
                              barmode='group', title=f"Predicted Outcomes from Lap {analysis_lap}")
            fig_prob.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#161b22', height=400)
            st.plotly_chart(fig_prob, use_container_width=True)

# --- BOTTOM ROW: THE GAPPER & AI ---
st.markdown("---")
row3_c1, row3_c2 = st.columns([2, 1])

with row3_c1:
    st.subheader("⏱️ The 'Gapper' (Delta to Leader)")
    st.markdown("Cumulative time gap to the race leader (Crucial for Undercut analysis).")
    
    if not history_df.empty:
        # Get the leader's time per lap
        leader_times = history_df.groupby('LapNumber')['LapTime'].min().reset_index()
        leader_times = leader_times.rename(columns={'LapTime': 'LeaderTime'})
        
        gap_df = pd.merge(history_df, leader_times, on='LapNumber')
        gap_df['Delta'] = gap_df['LapTime'] - gap_df['LeaderTime']
        gap_df['CumulativeGap'] = gap_df.groupby('Driver')['Delta'].cumsum()
        
        fig_gap = px.line(gap_df[gap_df['Driver'].isin(top_drivers)], x="LapNumber", y="CumulativeGap", color="Driver")
        fig_gap.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#161b22', 
                              yaxis_title="Seconds behind Leader", xaxis_title="Lap", height=350)
        # Invert Y axis so leader is at top (0)
        fig_gap.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_gap, use_container_width=True)

with row3_c2:
    st.subheader("🤖 AI Pit Wall Intel")
    win_p = probs.get(focal_driver, {}).get('win_prob', 0.0) if 'probs' in locals() else 0.0
    context = {
        'driver': focal_driver,
        'compound': focal_data.get('Compound', 'Unknown'),
        'tyre_life': focal_data.get('TyreLife', 0),
        'lap_time': focal_data.get('LapTime', 0.0),
        'win_prob': win_p
    }
    
    with st.spinner("AI Synthesizing Strategy..."):
        # Dummy RMSE since we aren't running the full predictive tracker loop here
        ai_msg = ai.generate_live_commentary(analysis_lap, context, 0.0)
        
    st.markdown(f"""
    <div style="background-color:#161b22; padding:20px; border-radius:10px; border: 1px solid #30363d; height:350px;">
        <h4 style="color:#ff1801; margin-top:0;">{focal_driver} Strategy Brief (Lap {analysis_lap})</h4>
        <p style="font-size:16px;">"{ai_msg}"</p>
        <hr style="border-color:#30363d;">
        <small><b>Model Confidence:</b> High (Monte Carlo Backed)</small><br>
        <small><b>Target Objective:</b> Maximize Points</small>
    </div>
    """, unsafe_allow_html=True)
