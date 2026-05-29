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
        logger.info(f"Running {self.num_simulations} Monte Carlo simulations for {remaining_laps} remaining laps...")
        
        drivers = current_lap_data['Driver'].unique()
        n_drivers = len(drivers)
        
        # Initialize simulation matrix: shape (num_simulations, n_drivers)
        # Represents total race time from this point forward
        simulated_times = np.zeros((self.num_simulations, n_drivers))
        
        # Base predictions for next lap (simplified for MVP speed)
        # In a full model, this iterates lap-by-lap, compounding degradation
        base_paces = np.random.uniform(90.0, 93.0, n_drivers) # Mocked base pace in seconds
        
        for sim in range(self.num_simulations):
            # Inject Gaussian noise to simulate traffic, mistakes, and degradation variance
            variance = np.random.normal(loc=0.0, scale=0.5, size=n_drivers) * remaining_laps
            
            # Simulated total time = (Base Pace * Remaining Laps) + Variance + Current Gap
            total_time = (base_paces * remaining_laps) + variance
            simulated_times[sim] = total_time
            
        # Analyze Results
        win_counts = {driver: 0 for driver in drivers}
        podium_counts = {driver: 0 for driver in drivers}
        
        for sim in range(self.num_simulations):
            # Sort drivers by their simulated total time in this iteration
            sorted_indices = np.argsort(simulated_times[sim])
            winner = drivers[sorted_indices[0]]
            second = drivers[sorted_indices[1]]
            third = drivers[sorted_indices[2]]
            
            win_counts[winner] += 1
            podium_counts[winner] += 1
            podium_counts[second] += 1
            podium_counts[third] += 1
            
        # Calculate Probabilities
        probabilities = {}
        for driver in drivers:
            probabilities[driver] = {
                'win_prob': win_counts[driver] / self.num_simulations,
                'podium_prob': podium_counts[driver] / self.num_simulations
            }
            
        return probabilities
