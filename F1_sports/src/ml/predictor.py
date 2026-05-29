import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from src.config import MODEL_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)

class RacePredictor:
    """
    Predicts tire degradation and lap time trends using XGBoost.
    """
    def __init__(self):
        self.model = xgb.XGBRegressor(
            n_estimators=100, 
            learning_rate=0.05, 
            max_depth=5, 
            objective='reg:squarederror'
        )
        self.label_encoders = {}
        self.is_trained = False

    def preprocess(self, df: pd.DataFrame):
        """Prepare F1 telemetry/laps data for training."""
        logger.info("Preprocessing telemetry data...")
        
        # In the new merged dataframe, we have multi-row telemetry per lap.
        # For lap-time prediction, we MUST aggregate to one row per (Driver, LapNumber).
        if 'LapNumber' in df.columns and 'X' in df.columns:
            logger.info("Aggregating high-frequency telemetry to lap-level features...")
            agg_dict = {
                'TyreLife': 'first',
                'Compound': 'first',
                'Speed': 'mean'
            }
            # Use the exact LapTime if available, else fallback to max Time telemetry
            if 'LapTime' in df.columns:
                agg_dict['LapTime'] = 'first'
            elif 'Time' in df.columns:
                agg_dict['Time'] = 'max'
                
            df = df.groupby(['Driver', 'LapNumber']).agg(agg_dict).reset_index()
            
            # Rename fallback if needed
            if 'Time' in df.columns and 'LapTime' not in df.columns:
                df = df.rename(columns={'Time': 'LapTime'})

        features = ['LapNumber', 'TyreLife', 'Compound']
        target = 'LapTime'
        
        if target not in df.columns:
            logger.error(f"Target column '{target}' is missing from data.")
            return pd.DataFrame(), pd.Series()
        
        # Clean data: drop rows with missing targets or missing key features
        df_clean = df.dropna(subset=[target] + features).copy()
        
        # Encode categorical variables
        if 'Compound' in features:
            le = LabelEncoder()
            # Ensure compound is string and handled consistently
            df_clean['Compound'] = le.fit_transform(df_clean['Compound'].astype(str))
            self.label_encoders['Compound'] = le
            
        X = df_clean[features]
        y = df_clean[target]
        return X, y

    def train(self, laps_parquet_path: str):
        """Train the model on the historical/session laps data and return metrics."""
        logger.info(f"Loading data from {laps_parquet_path}")
        try:
            df = pd.read_parquet(laps_parquet_path)
            X, y = self.preprocess(df)
            
            if X.empty:
                logger.error("Preprocessed features are empty. Cannot train.")
                return None

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            logger.info("Training XGBoost model for LapTime predictions...")
            eval_set = [(X_train, y_train), (X_test, y_test)]
            self.model.fit(
                X_train, y_train, 
                eval_set=eval_set, 
                verbose=False
            )
            self.is_trained = True
            
            # Gather metrics
            results = self.model.evals_result()
            train_rmse = results['validation_0']['rmse']
            test_rmse = results['validation_1']['rmse']
            
            importance = self.model.feature_importances_
            feature_names = X.columns.tolist()
            
            score = self.model.score(X_test, y_test)
            logger.info(f"Model trained. R^2 Score: {score:.3f}")
            
            # Save the model artifact
            model_path = MODEL_DIR / "lap_time_model.json"
            self.model.save_model(model_path)
            
            return {
                "r2_score": score,
                "train_rmse": train_rmse,
                "test_rmse": test_mse,
                "importance": dict(zip(feature_names, importance))
            }
            
        except Exception as e:
            logger.error(f"Error during training: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def predict_lap_time(self, lap_number: int, tyre_life: int, compound: str) -> float:
        """Infer lap time based on input features."""
        if not self.is_trained:
            logger.warning("Model not trained yet. Unable to predict.")
            return 0.0
        
        try:
            comp_encoded = self.label_encoders.get('Compound').transform([str(compound)])[0]
            X_infer = pd.DataFrame({
                'LapNumber': [lap_number],
                'TyreLife': [tyre_life],
                'Compound': [comp_encoded]
            })
            pred = self.model.predict(X_infer)
            return float(pred[0])
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return 0.0
