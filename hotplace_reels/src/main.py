import asyncio
from fastapi import FastAPI
import uvicorn
from src.bot.telegram_handler import get_bot_app
from src.core.config import settings
import logging
import threading

from src.scheduler.autonomous_agent import run_scheduler
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Seoul Hot Place AI Server")

@app.get("/health")
def health():
    return {"status": "running"}

def run_bot():
    logger.info("Starting Telegram Bot...")
    bot_app = get_bot_app()
    bot_app.run_polling()

if __name__ == "__main__":
    # 1. Start Telegram Bot in a separate thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # 2. Start Autonomous Scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # 3. Start FastAPI Server
    logger.info("Starting FastAPI Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
