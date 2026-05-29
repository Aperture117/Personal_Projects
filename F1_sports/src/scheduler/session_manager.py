from apscheduler.schedulers.background import BackgroundScheduler
import requests
from src.utils.logger import get_logger
from src.utils.notifications import NotificationManager
from src.config import CHECK_INTERVAL_MINUTES

logger = get_logger(__name__)

class SessionManager:
    """
    Monitors F1 schedule to detect upcoming and live sessions.
    Activates the necessary pipelines when a session goes live.
    """
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.notifier = NotificationManager()
        self.is_session_active = False
        self.current_session_info = None

    def check_schedule(self):
        """Checks the OpenF1 API for live or upcoming F1 sessions."""
        logger.info("Checking F1 schedule for live sessions...")
        try:
            # Check for live sessions (using OpenF1 status API)
            response = requests.get("https://api.openf1.org/v1/sessions?year=2024")
            if response.status_code == 200:
                sessions = response.json()
                if sessions:
                    latest_session = sessions[-1]
                    session_name = latest_session.get('session_name', 'Unknown')
                    location = latest_session.get('location', 'Unknown')
                    
                    # If it's a new session we haven't notified about yet
                    if not self.is_session_active:
                        logger.info(f"Detected NEW session: {session_name} at {location}")
                        self.is_session_active = True
                        self.current_session_info = latest_session
                        
                        # Send Telegram Notification
                        self.notifier.notify_session_start(latest_session)
                    
            else:
                logger.error(f"Failed to fetch schedule. HTTP Status: {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching session schedule: {e}")

    def start(self):
        """Starts the scheduler in the background."""
        self.scheduler.add_job(self.check_schedule, 'interval', minutes=CHECK_INTERVAL_MINUTES)
        self.scheduler.start()
        # Trigger an immediate run
        self.check_schedule()
        logger.info("Session Manager started.")
