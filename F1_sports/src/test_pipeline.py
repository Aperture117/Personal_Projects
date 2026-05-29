import sys
from pathlib import Path
import pandas as pd

# Setup path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.ingestion.telemetry import TelemetryIngestion
from src.ml.predictor import RacePredictor
from src.utils.logger import get_logger

logger = get_logger("TestPipeline")

def test_full_pipeline():
    logger.info("Starting Full Pipeline Verification Test...")
    
    # 1. Test Ingestion
    ingestion = TelemetryIngestion()
    path = ingestion.fetch_session_data(2024, 'Bahrain', 'R')
    
    if not path or not path.exists():
        logger.error("❌ Step 1 Failed: Data ingestion produced no file.")
        return False
    
    logger.info("✅ Step 1 Success: Data ingested and saved as Parquet.")
    
    # 2. Test ML Training with Visual Metrics
    predictor = RacePredictor()
    metrics = predictor.train(str(path))
    
    if not metrics:
        logger.error("❌ Step 2 Failed: Training returned no metrics.")
        return False
        
    logger.info("✅ Step 2 Success: Model trained with full metrics.")
    logger.info(f"   - R2 Score: {metrics['r2_score']:.4f}")
    logger.info(f"   - Final Test RMSE: {metrics['test_rmse'][-1]:.4f}")
    logger.info(f"   - Features: {list(metrics['importance'].keys())}")
    
    # 3. Test Prediction Logic
    pred = predictor.predict_lap_time(lap_number=10, tyre_life=5, compound='SOFT')
    if pred <= 0:
        logger.error("❌ Step 3 Failed: Model produced invalid prediction.")
        return False
        
    logger.info(f"✅ Step 3 Success: Model produced valid prediction: {pred:.2f}s")
    
    logger.info("🚀 ALL PIPELINE TESTS PASSED!")
    return True

if __name__ == "__main__":
    test_full_pipeline()
