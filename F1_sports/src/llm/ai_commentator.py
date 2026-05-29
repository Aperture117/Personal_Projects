import ollama
from src.config import OLLAMA_HOST, OLLAMA_MODEL
from src.utils.logger import get_logger

logger = get_logger(__name__)

class AICommentator:
    """
    Generates real-time, race-engineer style commentary during the historical replay.
    Uses local LLMs (Ollama) to synthesize telemetry, predictions, and accuracy metrics.
    """
    def __init__(self):
        self.model = OLLAMA_MODEL
        try:
            self.client = ollama.Client(host=OLLAMA_HOST)
            logger.info(f"AI Commentator initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {e}")
            self.client = None

    def generate_live_commentary(self, lap: int, driver_data: dict, model_rmse: float) -> str:
        """
        Generates tactical insights based on the simulated live state.
        """
        if not self.client:
            return "[AI Offline] Check Ollama service."

        # Constructing a rich prompt combining live data + prediction metrics
        prompt = f"""
        You are the Head Race Strategist for an F1 team.
        You are watching a historical replay of a race. It is currently Lap {lap}.
        
        Live Telemetry Context (Focal Driver):
        - Driver: {driver_data.get('driver', 'Unknown')}
        - Tyre Compound: {driver_data.get('compound', 'Unknown')}
        - Tyre Life: {driver_data.get('tyre_life', 0)} laps
        - Current Lap Time: {driver_data.get('lap_time', 0.0):.2f}s
        - Predicted Next Lap: {driver_data.get('predicted_next', 0.0):.2f}s
        - Model Confidence: {driver_data.get('confidence', 0.0)*100:.1f}% (RMSE: {model_rmse:.3f})

        Based on this data, provide a very brief (1-2 sentences) radio message to the driver or pit wall.
        Focus on tire degradation, predicted pace, or pit stop windows. 
        Be professional, analytical, and direct.
        
        Message:
        """

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                stream=False,
                options={'temperature': 0.3} # Low temp for analytical consistency
            )
            return response.get('response', 'No commentary generated.').strip()
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return "Strategy model busy. Keep pushing."
