import logging
import os
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Bot
from src.core.config import settings

logger = logging.getLogger(__name__)

# Global state for pending publications
PENDING_POSTS = {}

async def send_approval_message(image_paths: list[str], caption: str, target_chat_id: str = None):
    """
    Sends ONLY the image album and approval buttons to Telegram.
    """
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        chat_id = target_chat_id or settings.ALLOWED_TELEGRAM_USER_IDS.split(',')[0]
        
        post_id = f"post_{int(time.time())}"
        PENDING_POSTS[post_id] = {"images": image_paths, "caption": caption}
        
        media = []
        opened_files = []
        
        for i, path in enumerate(image_paths[:10]):
            if os.path.exists(path):
                f = open(path, 'rb')
                opened_files.append(f)
                # No captions on individual images per request
                media.append(InputMediaPhoto(f))
        
        if media:
            try:
                # 1. Send Image Album
                await bot.send_media_group(chat_id=chat_id, media=media)
                
                # 2. Send simple approval message with buttons
                keyboard = [
                    [InlineKeyboardButton("✅ 인스타 발행 승인", callback_data=f"approve_pub_{post_id}")],
                    [InlineKeyboardButton("❌ 품질 불량 (거절)", callback_data=f"reject_pub_{post_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await bot.send_message(
                    chat_id=chat_id, 
                    text="✨ <b>비주얼 생성이 완료되었습니다.</b>\n위 사진들을 확인하고 승인 버튼을 눌러주세요.",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                
                logger.info("✅ Telegram Visual Report Sent (Images Only).")
                return True
            finally:
                for f in opened_files:
                    f.close()
        return False
    except Exception as e:
        logger.error(f"💥 Messaging Error: {e}")
        return False
