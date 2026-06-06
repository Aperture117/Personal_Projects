import asyncio
import schedule
import time
import logging
from src.core.config import settings
from src.agents.orchestrator import batch_orchestrator

logger = logging.getLogger(__name__)

class AutonomousAgent:
    def __init__(self):
        self.user_id = settings.ALLOWED_TELEGRAM_USER_IDS.split(",")[0]

    async def run_autonomous_batch(self):
        """Trigger the full Batch OS cycle autonomously."""
        logger.info("🤖 Autonomous Agent: Starting 3-hour Batch OS cycle...")
        await batch_orchestrator.run_batch(niche=None)

def run_scheduler():
    agent = AutonomousAgent()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Run a full batch every 3 hours
    schedule.every(3).hours.do(lambda: loop.run_until_complete(agent.run_autonomous_batch()))

    logger.info("📅 Autonomous Scheduler Started: Batch OS Active (Every 3 Hours).")
    while True:
        schedule.run_pending()
        time.sleep(10)
