from src.engine.telemetry_streamer import TelemetryStreamer
from pathlib import Path

class ReplayEngine:
    """
    Core engine to manage the state of a historical replay.
    Handles the concept of 'current time/lap' and provides the data slice.
    """
    def __init__(self, data_path: Path):
        self.streamer = TelemetryStreamer(data_path)
        self.current_lap = 1
        self.is_playing = False
        
    @property
    def max_laps(self) -> int:
        return self.streamer.max_laps

    def next_lap(self):
        """Advances the replay by one lap."""
        if self.current_lap < self.max_laps:
            self.current_lap += 1
            
    def set_lap(self, lap: int):
        """Seeks to a specific lap in the replay."""
        if 1 <= lap <= self.max_laps:
            self.current_lap = lap

    def get_current_state(self):
        """Returns the data for the currently active lap."""
        return self.streamer.get_lap_data(self.current_lap)
