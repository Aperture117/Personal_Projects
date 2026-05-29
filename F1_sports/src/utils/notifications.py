import requests
import os
from src.utils.logger import get_logger
from dotenv import load_dotenv

load_dotenv()
logger = get_logger(__name__)

class NotificationManager:
    """
    Handles sending notifications to the user via Telegram.
    """
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.is_enabled = bool(self.bot_token and self.chat_id)
        
        if not self.is_enabled:
            logger.warning("Telegram notifications are disabled. Missing Token or Chat ID.")

    def send_message(self, message: str):
        """Sends a text message to the configured Telegram chat."""
        if not self.is_enabled:
            return

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                logger.info("Telegram notification sent successfully.")
            else:
                logger.error(f"Failed to send Telegram message: {response.text}")
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")

    def notify_session_start(self, session_info: dict):
        """Specifically formatted notification for a session starting."""
        msg = (
            f"🏎️ **F1 Live Session Detected!**\n\n"
            f"📍 **Location:** {session_info.get('location', 'Unknown')}\n"
            f"🏁 **Session:** {session_info.get('session_name', 'Unknown')}\n"
            f"⏰ **Status:** Live streaming and AI analysis activated.\n\n"
            f"🔗 Check your dashboard: http://localhost:8501"
        )
        self.send_message(msg)

    def notify_strategy_alert(self, driver: str, alert_type: str, recommendation: str):
        """Alert for critical race events (Undercut, Tire Wear, etc.)"""
        msg = (
            f"⚠️ **Race Strategy Alert: {driver}**\n\n"
            f"🔍 **Event:** {alert_type}\n"
            f"💡 **AI Recommendation:** {recommendation}\n"
        )
        self.send_message(msg)
