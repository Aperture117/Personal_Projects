import asyncio
import schedule
import time
from src.services.trend_intelligence import trend_intelligence
from src.core.config import settings
from telegram import Bot
import logging

logger = logging.getLogger(__name__)

class AutonomousAgent:
    def __init__(self):
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        self.user_id = settings.ALLOWED_TELEGRAM_USER_IDS.split(",")[0]

    async def daily_autonomous_scan(self):
        """
        Daily task: Find hot region and report to user.
        """
        logger.info("🤖 Starting daily autonomous trend scan...")
        hot_region = trend_intelligence.scan_nationwide_trends()
        
        msg = f"🌅 **오늘의 핫플레이스 탐지 결과**\n\n"
        msg += f"📍 오늘 가장 뜨거운 지역: **{hot_region['district']}**\n"
        msg += f"📊 소셜 언급량: {hot_region['total_mentions']}건\n\n"
        msg += f"이 지역의 TOP 5 장소를 분석하고 릴스 대본을 만들까요?"
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [[InlineKeyboardButton("✅ 분석 및 콘텐츠 생성 시작", callback_data=f"start_curation_{hot_region['district']}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.bot.send_message(chat_id=self.user_id, text=msg, reply_markup=reply_markup, parse_mode='Markdown')

def run_scheduler():
    agent = AutonomousAgent()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Schedule for 09:00 AM
    schedule.every().day.at("09:00").do(lambda: loop.run_until_complete(agent.daily_autonomous_scan()))
    
    logger.info("📅 Autonomous Scheduler Started (09:00 AM Daily)")
    while True:
        schedule.run_pending()
        time.sleep(60)
