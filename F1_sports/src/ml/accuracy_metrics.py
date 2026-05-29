import numpy as np

def calculate_rmse(predictions: list, actuals: list) -> float:
    """
    Calculates the Root Mean Squared Error (RMSE) for lap time predictions.
    """
    if not predictions or not actuals or len(predictions) != len(actuals):
        return 0.0
    
    pred_arr = np.array(predictions)
    act_arr = np.array(actuals)
    
    mse = np.mean((pred_arr - act_arr) ** 2)
    return float(np.sqrt(mse))

def calculate_drift(previous_pred: float, current_pred: float) -> float:
    """
    Measures how much a prediction has shifted from the previous lap.
    Positive means time increased, negative means time decreased.
    """
    if previous_pred is None or current_pred is None:
        return 0.0
    return float(current_pred - previous_pred)

def calculate_confidence(drift: float, base_confidence: float = 0.95) -> float:
    """
    Estimates prediction confidence based on volatility/drift.
    High drift -> lower confidence.
    """
    penalty = min(abs(drift) * 0.1, 0.5) # Max 50% penalty
    return max(base_confidence - penalty, 0.1)
