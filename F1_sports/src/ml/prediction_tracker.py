import pandas as pd
from src.ml.accuracy_metrics import calculate_rmse, calculate_drift, calculate_confidence
from src.utils.logger import get_logger

logger = get_logger(__name__)

class PredictionTracker:
    """
    Continuously runs prediction models per lap and evaluates their accuracy 
    against the actual telemetry arriving in the stream.
    """
    def __init__(self):
        self.history = {}  # Format: {driver: {lap: {'predicted': float, 'actual': float, 'confidence': float}}}
        self.global_rmse = 0.0

    def predict_lap(self, current_lap: int, telemetry_df: pd.DataFrame):
        """
        Simulates running the ML model on the current data to predict the NEXT lap.
        For MVP simulation, we use a simple heuristic based on current lap time + expected deg.
        """
        predictions = {}
        for _, row in telemetry_df.iterrows():
            driver = row['Driver']
            current_time = row['LapTime']
            tyre_life = row['TyreLife']
            
            # Skip invalid data
            if pd.isna(current_time) or pd.isna(tyre_life):
                continue
                
            if driver not in self.history:
                self.history[driver] = {}
                
            # Simulated ML Prediction: Expected slight degradation next lap
            # In a full deployment, this calls self.xgboost_model.predict()
            expected_deg = 0.05 if tyre_life < 15 else 0.15
            predicted_next_lap = current_time + expected_deg
            
            # Calculate drift and confidence
            prev_lap = current_lap - 1
            prev_pred = self.history[driver].get(prev_lap, {}).get('predicted', predicted_next_lap)
            drift = calculate_drift(prev_pred, predicted_next_lap)
            confidence = calculate_confidence(drift)
            
            # Store prediction for NEXT lap
            self.history[driver][current_lap + 1] = {
                'predicted': predicted_next_lap,
                'actual': None,
                'confidence': confidence,
                'drift': drift
            }
            predictions[driver] = predicted_next_lap
            
        return predictions

    def evaluate(self, current_lap: int, telemetry_df: pd.DataFrame):
        """
        Compares the actual data of the current lap against what was predicted on the previous lap.
        """
        all_preds = []
        all_actuals = []
        
        for _, row in telemetry_df.iterrows():
            driver = row['Driver']
            actual_time = row['LapTime']
            
            if pd.isna(actual_time) or driver not in self.history or current_lap not in self.history[driver]:
                continue
                
            # Update actuals
            self.history[driver][current_lap]['actual'] = actual_time
            
            pred_time = self.history[driver][current_lap]['predicted']
            all_preds.append(pred_time)
            all_actuals.append(actual_time)
            
        # Update Global RMSE metric
        if all_preds and all_actuals:
            self.global_rmse = calculate_rmse(all_preds, all_actuals)
            
        return self.global_rmse
