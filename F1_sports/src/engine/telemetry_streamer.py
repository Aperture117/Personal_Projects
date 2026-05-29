import pandas as pd
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

class TelemetryStreamer:
    """
    Simulates a live telemetry stream by yielding historical data lap-by-lap.
    Reads from optimized Parquet storage.
    """
    def __init__(self, data_path: Path):
        self.data_path = data_path
        self.df = None
        self.max_laps = 0
        self.drivers = []
        self._load_data()

    def _load_data(self):
        """Loads and pre-processes the parquet dataset for streaming."""
        if not self.data_path.exists():
            logger.error(f"Data file not found: {self.data_path}")
            return
            
        logger.info(f"Loading replay data from {self.data_path}")
        self.df = pd.read_parquet(self.data_path)
        
        # Clean up data for replay
        self.df = self.df.dropna(subset=['LapNumber', 'Driver'])
        self.df['LapNumber'] = self.df['LapNumber'].astype(int)
        
        self.max_laps = self.df['LapNumber'].max()
        self.drivers = self.df['Driver'].unique().tolist()
        logger.info(f"Loaded {self.max_laps} laps for {len(self.drivers)} drivers.")

    def get_lap_data(self, lap_number: int) -> pd.DataFrame:
        """
        Retrieves the telemetry slice for a specific lap.
        Simulates the data payload received during a live race.
        """
        if self.df is None:
            return pd.DataFrame()
            
        return self.df[self.df['LapNumber'] == lap_number].copy()
