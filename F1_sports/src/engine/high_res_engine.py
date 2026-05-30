import pandas as pd
import numpy as np
from src.utils.logger import get_logger

logger = get_logger(__name__)

class HighResReplayEngine:
    """
    High-resolution engine that streams telemetry at sub-lap intervals.
    Provides smooth position updates for real-time visualization.
    """
    def __init__(self, full_data_path: str):
        logger.info(f"Initializing High-Res Engine with {full_data_path}")
        self.df = pd.read_parquet(full_data_path)
        
        # Sort by SessionTime to ensure linear progression
        self.df = self.df.sort_values(by='Time').reset_index(drop=True)
        
        # Get unique timestamps to iterate through
        self.timestamps = self.df['Time'].unique()
        self.current_idx = 0
        self.max_idx = len(self.timestamps) - 1

    def get_next_step(self):
        """Returns the telemetry slice for the next available timestamp."""
        if self.current_idx <= self.max_idx:
            ts = self.timestamps[self.current_idx]
            slice_df = self.df[self.df['Time'] == ts]
            self.current_idx += 1
            return slice_df, ts
        return None, None

    def seek_to_lap(self, lap_number: int):
        """Jumps the engine to the start of a specific lap."""
        lap_start = self.df[self.df['LapNumber'] == lap_number]
        if not lap_start.empty:
            start_time = lap_start['Time'].min()
            # Find closest index in timestamps
            self.current_idx = np.searchsorted(self.timestamps, start_time)

    @property
    def current_lap(self):
        """Heuristic to get current lap number from the active pointer."""
        if self.current_idx <= self.max_idx:
            return int(self.df.iloc[self.current_idx]['LapNumber'])
        return 1

    @property
    def total_steps(self):
        return len(self.timestamps)
