import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from src.config import MODEL_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)

class RacePredictor:
    def __init__(self):
        self.model = None
        self.label_encoders = {}
        self.is_trained = False

    def preprocess(self, df: pd.DataFrame):
        # Data is already aggregated to lap-level by TelemetryIngestion for efficiency
        features = ['LapNumber', 'TyreLife', 'Compound']
        target = 'LapTime'
        
        df_clean = df.dropna(subset=[target] + features).copy()
        
        if 'Compound' in features:
            le = LabelEncoder()
            df_clean['Compound'] = le.fit_transform(df_clean['Compound'].astype(str))
            self.label_encoders['Compound'] = le
            
        X = df_clean[features]
        y = df_clean[target]
        return X, y

    def train_visual(self, laps_parquet_path: str, progress_ui_callback=None):
        """
        Trains the model incrementally and reports progress to the UI.
        """
        try:
            df = pd.read_parquet(laps_parquet_path)
            X, y = self.preprocess(df)
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            dtrain = xgb.DMatrix(X_train, label=y_train)
            dtest = xgb.DMatrix(X_test, label=y_test)
            
            params = {
                'max_depth': 5,
                'eta': 0.1,
                'objective': 'reg:squarederror',
                'eval_metric': 'rmse'
            }
            
            self.history = {'train': [], 'test': []}
            self.model = None
            
            # Incremental training for UI visualization
            num_boost_round = 50
            for i in range(num_boost_round):
                self.model = xgb.train(
                    params, dtrain, 
                    num_boost_round=1, 
                    xgb_model=self.model
                )
                
                # Evaluate
                train_res = self.model.eval(dtrain)
                test_res = self.model.eval(dtest)
                
                # Parse RMSE from string like "[0]\ttrain-rmse:1.2345"
                train_rmse = float(train_res.split(':')[-1])
                test_rmse = float(test_res.split(':')[-1])
                
                self.history['train'].append(train_rmse)
                self.history['test'].append(test_rmse)
                
                if progress_ui_callback:
                    progress_ui_callback(i + 1, num_boost_round, self.history)
            
            self.is_trained = True
            
            # Feature importance
            importance = self.model.get_score(importance_type='weight')
            # Map encoded features back to names
            mapped_importance = {feat: importance.get(feat, 0) for feat in X.columns}
            
            return {
                "history": self.history,
                "importance": mapped_importance
            }
            
        except Exception as e:
            logger.error(f"Visual training failed: {e}")
            return None

    def predict_lap_time(self, lap_number: int, tyre_life: int, compound: str) -> float:
        if not self.is_trained or not self.model:
            return 0.0
        try:
            comp_encoded = self.label_encoders.get('Compound').transform([str(compound)])[0]
            X_infer = pd.DataFrame({
                'LapNumber': [lap_number],
                'TyreLife': [tyre_life],
                'Compound': [comp_encoded]
            })
            dmatrix = xgb.DMatrix(X_infer)
            pred = self.model.predict(dmatrix)
            return float(pred[0])
        except:
            return 0.0
