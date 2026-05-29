import ollama
from src.config import OLLAMA_HOST, OLLAMA_MODEL
from src.utils.logger import get_logger

logger = get_logger(__name__)

class RaceStrategist:
    """
    Uses local LLMs (Ollama) to generate race engineer style commentary.
    """
    def __init__(self):
        self.model = OLLAMA_MODEL
        try:
            # Connect to local Ollama instance
            self.client = ollama.Client(host=OLLAMA_HOST)
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            self.client = None

    def generate_commentary(self, telemetry_summary: dict) -> str:
        """
        Takes real-time telemetry metrics and outputs an engineer's strategic assessment.
        """
        if not self.client:
            return "Strategy AI is currently offline (Ollama client unavailable)."

        prompt = f"""
        You are the Head Race Strategist for an F1 team. 
        Analyze the following live race telemetry summary and give a concise, confident, 2-3 sentence strategic recommendation.
        Act like you are speaking over the team radio. Keep it professional, analytical, and short.
        
        Current Situation:
        - Lead Driver Tyres: {telemetry_summary.get('tyre_compound', 'Unknown')} (Life: {telemetry_summary.get('tyre_life', 0)} laps)
        - Average Lap Time Trend: {telemetry_summary.get('lap_time_trend', 'Stable')}
        - Track Status: {telemetry_summary.get('track_status', 'Clear')}
        - Weather: {telemetry_summary.get('weather', 'Dry')}
        - Key Event: {telemetry_summary.get('key_event', 'None')}

        Recommendation:
        """

        try:
            logger.info(f"Generating strategy commentary using {self.model}...")
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                stream=False
            )
            return response.get('response', 'No strategy response generated.').strip()
        except Exception as e:
            logger.error(f"Error during LLM inference: {e}")
            return "Unable to connect to the local strategy model. Ensure Ollama is running."
