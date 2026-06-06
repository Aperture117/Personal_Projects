import logging
import os
from telegram import Bot
from src.core.config import settings

logger = logging.getLogger(__name__)

async def send_status_update(message: str):
    """
    Sends a simple status update message to the user on Telegram.
    Used for tracking batch progress.
    """
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        chat_id = settings.ALLOWED_TELEGRAM_USER_IDS.split(',')[0]
        await bot.send_message(chat_id=chat_id, text=f"ℹ️ <b>[Batch Status]</b>: {message}", parse_mode='HTML')
        logger.info(f"📲 Status Notification Sent: {message}")
    except Exception as e:
        logger.error(f"Failed to send status update: {e}")
