import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.scheduler.session_manager import SessionManager
from src.ingestion.telemetry import TelemetryIngestion
from src.ml.predictor import RacePredictor
from src.llm.strategist import RaceStrategist
from src.utils.logger import get_logger

logger = get_logger("PipelineRunner")

def main():
    logger.info("Starting F1 AI Pipeline MVP...")
    
    # 1. Initialize & Start Scheduler
    manager = SessionManager()
    manager.start()
    
    # 2. Ingest Data (Mock Live Session with Historical Bahrain Data)
    ingestion = TelemetryIngestion()
    data_path = ingestion.fetch_session_data(year=2024, race='Bahrain', session_type='R')
    
    if not data_path:
        logger.error("Data ingestion failed. Exiting pipeline.")
        return
        
    # 3. Train ML Predictive Pipeline
    predictor = RacePredictor()
    predictor.train(str(data_path))
    
    # Example Prediction for Lap 20, 15 Laps old SOFT tires
    pred_time = predictor.predict_lap_time(lap_number=20, tyre_life=15, compound='SOFT')
    logger.info(f"Predicted Lap Time for 15-lap old SOFT tire: {pred_time}s")
    
    # 4. Generate AI Strategy Context (Sample execution)
    strategist = RaceStrategist()
    sample_context = {
        'tyre_compound': 'SOFT',
        'tyre_life': 18,
        'lap_time_trend': 'Degrading rapidly (+0.8s vs average)',
        'track_status': 'Yellow Sector 2',
        'weather': 'Dry',
        'key_event': 'Pit window open for undercut'
    }
    
    commentary = strategist.generate_commentary(sample_context)
    logger.info(f"AI Strategist Output: {commentary}")
    
    logger.info("Pipeline executed successfully. Start the Streamlit UI with `streamlit run app/Home.py`")

if __name__ == "__main__":
    main()
