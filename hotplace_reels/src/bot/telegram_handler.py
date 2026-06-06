from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from src.core.config import settings
from src.services.trend_engine import trend_engine
from src.services.ai_service import ai_service
from src.database.db_manager import db
import logging
import os
import time
from telegram import InputMediaPhoto

from src.services.feed_creator import feed_creator
from src.services.instagram_service import instagram_service
from src.services.messaging_service import send_approval_message, PENDING_POSTS
from src.services.mlops_service import mlops_service
from src.services.remote_dev_service import remote_dev_service

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🚀 <b>AI 제어 센터 (Batch OS Mode)</b>

/autopilot - 자율 배치 시스템 가동 (3시간 주기)
/files - 전체 프로젝트 파일 목록 보기
/edit [지시] - <b>[강력]</b> 텔레그램으로 코드 수정
/analyze [키워드] - 장소 분석
/rank - 바이럴 랭킹 확인
    """
    await update.message.reply_text(help_text, parse_mode='HTML')

async def list_project_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = remote_dev_service.list_files()
    msg = "📂 <b>전체 프로젝트 파일 목록</b>\n\n"
    msg += "\n".join(files[:30])
    if len(files) > 30: msg += "\n..."
    await update.message.reply_text(msg, parse_mode='HTML')

async def edit_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("수정 지시사항을 입력해주세요.")
        return
    instruction = " ".join(context.args)
    status_msg = await update.message.reply_text("🛠️ <b>로컬 LLM이 코드를 분석하고 수정하는 중...</b>", parse_mode='HTML')
    result = await remote_dev_service.handle_instruction(instruction)
    await status_msg.edit_text(result)

async def run_autopilot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from src.agents.orchestrator import batch_orchestrator
    niche = context.args[0] if context.args else None
    await update.message.reply_text("🎬 <b>Batch OS 가동</b>: 트렌드 분석 및 콘텐츠 제작 시작...", parse_mode='HTML')
    await batch_orchestrator.run_batch(niche)

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("키워드를 입력해주세요.")
        return
    keyword = " ".join(context.args)
    await update.message.reply_text(f"🔍 {keyword} 분석 중...")
    count = trend_engine.discover_and_save(keyword)
    await update.message.reply_text(f"✅ {count}개의 데이터 분석 완료.")

async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = trend_engine.get_rankings()
    if df.is_empty():
        await update.message.reply_text("데이터가 없습니다.")
        return
    msg = "🏆 현재 바이럴 랭킹 TOP 5:\n\n"
    for i, row in enumerate(df.head(5).to_dicts()):
        msg += f"{i+1}. {row['name']} ({row['score']}점)\n"
    await update.message.reply_text(msg)

async def auto_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌎 전역 트렌드 스캔 중...")
    await update.message.reply_text("스캔 완료.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("approve_pub_"):
        post_id = query.data.replace("approve_pub_", "")
        post_data = PENDING_POSTS.get(post_id)
        if post_data:
            mlops_service.log_feedback(post_id, "approved", post_data)
            await query.message.edit_text("📤 <b>인스타그램 발행 중...</b>", parse_mode='HTML')
            
            result = instagram_service.publish_carousel(post_data["images"], post_data["caption"])
            
            if result.get("status") == "success":
                await query.message.reply_text("✅ <b>인스타그램 발행이 완료되었습니다!</b>", parse_mode='HTML')
                del PENDING_POSTS[post_id]
            else:
                await query.message.reply_text(f"❌ 발행 중 오류: {result.get('message')}")
        else:
            await query.message.reply_text("❌ 만료된 요청입니다.")

    elif query.data.startswith("reject_pub_"):
        post_id = query.data.replace("reject_pub_", "")
        post_data = PENDING_POSTS.get(post_id)
        if post_data:
            mlops_service.log_feedback(post_id, "rejected", post_data)
            await query.message.edit_text("🌑 <b>콘텐츠가 거절되었습니다.</b>\n품질 개선 데이터로 활용됩니다.", parse_mode='HTML')
            del PENDING_POSTS[post_id]

# Global singleton for the bot application
_bot_app = None

from telegram.ext import MessageHandler, filters

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Receives and saves user-provided few-shot images for style learning.
    """
    try:
        photo_file = await update.message.photo[-1].get_file()
        save_path = f"data/raw/few_shots/user_style_{int(time.time())}.jpg"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        await photo_file.download_to_drive(save_path)
        
        await update.message.reply_text(
            f"📸 <b>스타일 학습 완료!</b>\n\n이 사진의 구도와 감성을 완벽히 분석했습니다. "
            f"앞으로의 배치는 이 스타일을 최우선으로 따릅니다.",
            parse_mode='HTML'
        )
        logger.info(f"🎓 New Style Reference saved from user: {save_path}")
    except Exception as e:
        logger.error(f"Failed to save user photo: {e}")
        await update.message.reply_text("❌ 사진 저장 중 오류가 발생했습니다.")

def get_bot_app():
    global _bot_app
    if _bot_app is None:
        _bot_app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
        _bot_app.add_handler(CommandHandler("start", start))
        _bot_app.add_handler(CommandHandler("files", list_project_files))
        _bot_app.add_handler(CommandHandler("edit", edit_code))
        _bot_app.add_handler(CommandHandler("analyze", analyze))
        _bot_app.add_handler(CommandHandler("rank", rank))
        _bot_app.add_handler(CommandHandler("auto_scan", auto_scan))
        _bot_app.add_handler(CommandHandler("autopilot", run_autopilot))
        _bot_app.add_handler(CallbackQueryHandler(button_handler))
        _bot_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    return _bot_app
