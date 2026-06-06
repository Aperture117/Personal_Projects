import sys
import os
sys.path.append(os.getcwd())

import asyncio
from fastapi import FastAPI
import uvicorn
from src.bot.telegram_handler import get_bot_app
from src.core.config import settings
import logging
import threading
from pydantic import BaseModel
from typing import List, Optional

from src.agents.orchestrator import batch_orchestrator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Creator Batch OS API")

class NicheRequest(BaseModel):
    niche: Optional[str] = None

@app.post("/agent/batch/run")
async def run_batch(req: NicheRequest):
    """Manually trigger a Batch OS production cycle."""
    asyncio.create_task(batch_orchestrator.run_batch(req.niche))
    return {"status": "batch_started", "niche": req.niche}

@app.get("/health")
def health():
    return {"status": "active", "mode": "Batch OS"}

from src.scheduler.autonomous_agent import run_scheduler

def run_bot():
    logger.info("Starting Telegram Bot Hub...")
    bot_app = get_bot_app()
    bot_app.run_polling()

if __name__ == "__main__":
    # 1. Start Autonomous Scheduler (Every 3 hours)
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # 2. Start Telegram Bot
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # 3. Start FastAPI Server
    logger.info("Starting AI Creator Batch OS Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
