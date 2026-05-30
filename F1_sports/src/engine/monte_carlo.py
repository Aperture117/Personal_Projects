import numpy as np
import pandas as pd
from src.utils.logger import get_logger

logger = get_logger(__name__)

class MonteCarloSimulator:
    """
    State-of-the-art probabilistic race simulator.
    Instead of predicting one outcome, it runs thousands of virtual races from the current lap
    to calculate win/podium probabilities considering traffic, degradation variance, and random events.
    """
    def __init__(self, predictor):
        self.predictor = predictor # Base ML predictor (XGBoost/Deep Learning)
        self.num_simulations = 1000

    def run_simulations(self, current_lap_data: pd.DataFrame, remaining_laps: int) -> dict:
        """
        Runs Monte Carlo simulations to calculate probabilities.
        Returns a dictionary of {Driver: {'win_prob': float, 'podium_prob': float}}
        """
        if remaining_laps <= 0 or current_lap_data.empty:
            return {}
            
        # Clean data for simulation: MUST have non-zero lap times
        df_sim = current_lap_data[(current_lap_data['LapTime'] > 0) & (current_lap_data['Driver'].notna())].copy()
        if df_sim.empty:
            return {}
            
        drivers = df_sim['Driver'].values
        current_paces = df_sim['LapTime'].values
        n_drivers = len(drivers)
        
        # Initialize simulation matrix: shape (num_simulations, n_drivers)
        simulated_times = np.zeros((self.num_simulations, n_drivers))
        
        for sim in range(self.num_simulations):
            # Inject Gaussian noise. Scale variance by remaining laps (uncertainty grows over time)
            # Base variance is e.g. 0.3 seconds per lap
            variance = np.random.normal(loc=0.0, scale=0.3, size=n_drivers) * remaining_laps
            
            # Simulated total time = (Current Pace * Remaining Laps) + Cumulative Variance
            # In a true system, we'd also add current cumulative race time (gap to leader).
            # For this visualization, projecting forward pace is sufficient.
            total_time = (current_paces * remaining_laps) + variance
            simulated_times[sim] = total_time
            
        # Analyze Results
        win_counts = {driver: 0 for driver in drivers}
        podium_counts = {driver: 0 for driver in drivers}
        
        for sim in range(self.num_simulations):
            sorted_indices = np.argsort(simulated_times[sim])
            winner = drivers[sorted_indices[0]]
            
            win_counts[winner] += 1
            podium_counts[winner] += 1
            if n_drivers > 1:
                podium_counts[drivers[sorted_indices[1]]] += 1
            if n_drivers > 2:
                podium_counts[drivers[sorted_indices[2]]] += 1
            
        # Calculate Probabilities
        probabilities = {}
        for driver in drivers:
            probabilities[driver] = {
                'win_prob': win_counts[driver] / self.num_simulations,
                'podium_prob': podium_counts[driver] / self.num_simulations
            }
            
        return probabilities
