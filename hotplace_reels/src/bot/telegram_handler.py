from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from src.core.config import settings
from src.services.trend_engine import trend_engine
from src.services.ai_service import ai_service
from src.database.db_manager import db
import logging

from src.services.media_downloader import media_downloader
from src.services.video_engine import video_creator
from src.services.trend_intelligence import trend_intelligence
from src.services.content_curator import content_curator
import os

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🚀 **hotplace_reels AI 제어 센터**

사용 가능한 명령어 리스트입니다:

🔍 **분석 및 발굴**
/auto_scan - 전국 핫플레이스 트렌드 자동 스캔
/analyze [지역명] - 특정 지역 장소 정밀 분석 (예: /analyze 성수동)

🏆 **랭킹 및 콘텐츠**
/rank - 현재 분석된 장소들의 바이럴 랭킹 확인
/rank [지역명] - 특정 지역의 랭킹만 확인

📱 **자동화**
매일 오전 09:00에 전국 트렌드 보고서가 자동으로 전송됩니다.

원하시는 명령어를 입력하거나 아래 버튼을 활용하세요!
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("키워드를 입력해주세요. 예: /analyze 성수동")
        return
    
    keyword = " ".join(context.args)
    await update.message.reply_text(f"🔍 {keyword} 분석 중...")
    
    count = trend_engine.discover_and_save(keyword)
    await update.message.reply_text(f"✅ {count}개의 장소를 분석하고 저장했습니다.")

async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    district = context.args[0] if context.args else None
    df = trend_engine.get_rankings(district=district)
    if df.is_empty():
        await update.message.reply_text("데이터가 없습니다. 먼저 /analyze를 실행하세요.")
        return
    
    msg = "🏆 현재 바이럴 랭킹 TOP 5:\n\n"
    for i, row in enumerate(df.head(5).to_dicts()):
        msg += f"{i+1}. {row['name']} ({row['score']}점)\n"
        msg += f"📍 {row['address']}\n\n"
        
    # Add buttons for content generation
    keyboard = []
    for row in df.head(3).to_dicts():
        keyboard.append([
            InlineKeyboardButton(f"🎬 {row['name']} 릴스", callback_data=f"gen_reels_{row['name']}"),
            InlineKeyboardButton(f"📸 {row['name']} 피드", callback_data=f"gen_feed_{row['name']}")
        ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(msg, reply_markup=reply_markup)

async def auto_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌎 전국 트렌드 데이터 분석 중... (수 분이 소요될 수 있습니다)")
    hot_regions = trend_intelligence.scan_nationwide_trends(limit=5)
    
    msg = "📊 **오늘의 전국 핫플레이스 리포트**\n\n"
    keyboard = []
    
    for i, region in enumerate(hot_regions):
        msg += f"{i+1}. **{region['district']}** (총 {region['total_mentions']}건)\n"
        msg += f"   └ 블로그: {region['blog_count']} | 뉴스: {region['news_count']}\n\n"
        
        keyboard.append([InlineKeyboardButton(f"✅ {region['district']} 릴스/피드 제작", callback_data=f"start_curation_{region['district']}")])
    
    msg += "콘텐츠를 제작할 지역을 선택해주세요!"
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("gen_reels_"):
        # Existing single-spot generation
        place_name = query.data.replace("gen_reels_", "")
        await query.message.reply_text(f"🤖 {place_name} 릴스 대본 생성 중...")
        content = ai_service.generate_content("reels", place_name, "Viral trend spike")
        await query.message.reply_text(f"📝 릴스 대본:\n\n{content}")

    elif query.data.startswith("gen_feed_"):
        place_name = query.data.replace("gen_feed_", "")
        await query.message.reply_text(f"🤖 {place_name} 피드 게시물 생성 중...")
        content = ai_service.generate_content("feed", place_name, "Viral trend spike")
        await query.message.reply_text(f"📸 **인스타 피드용 캡션 및 해시태그**\n\n{content}")

    elif query.data.startswith("start_curation_"):
        district = query.data.replace("start_curation_", "")
        await query.message.reply_text(f"🔍 {district} TOP 5 장소 정밀 분석 중...")
        
        # 1. Discover top 5 spots in the region
        trend_engine.discover_and_save(f"{district} 맛집")
        rankings = trend_engine.get_rankings()
        top_spots = rankings.head(5).to_dicts()
        
        # 2. Curate combined script
        await query.message.reply_text(f"✍️ {len(top_spots)}개 장소를 엮어 릴스 대본 작성 중...")
        script = content_curator.group_spots_for_reels(district, top_spots)
        
        # 3. Store in DB
        db.add_to_queue(f"{district} TOP 5", "reels_curation", script)
        
        # 4. Final Approval Buttons
        msg = f"🎬 {district} TOP 5 릴스 대본 완료\n\n{script}\n\n이 대본으로 영상을 제작할까요?"
        keyboard = [
            [InlineKeyboardButton("🚀 영상 제작 및 업로드 요청", callback_data=f"publish_ig_{district}")],
            [InlineKeyboardButton("❌ 반려", callback_data="reject_content")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            # Try sending with Markdown first
            await query.message.reply_text(msg, reply_markup=reply_markup)
        except Exception as e:
            # Fallback to plain text if Markdown parsing fails
            logger.warning(f"Markdown failed, falling back to plain text: {e}")
            await query.message.reply_text(msg, reply_markup=reply_markup)

    elif query.data.startswith("publish_ig_"):
        district = query.data.replace("publish_ig_", "")
        await query.message.reply_text(f"📸 {district} 관련 실제 이미지 수집 및 영상 렌더링 시작...")
        
        # 1. Get script from DB queue (latest for this district)
        # For simplicity, we'll re-generate or fetch the last item
        # In this implementation, let's assume we search images for the top spots
        rankings = trend_engine.get_rankings()
        top_spots = rankings.head(5).to_dicts()
        
        all_image_paths = []
        for spot in top_spots:
            img_urls = trend_engine.naver.search_images(spot['name'], display=2)
            paths = media_downloader.download_images(spot['name'], img_urls)
            all_image_paths.extend(paths)
        
        # 2. Render Video with these images
        # We need the script again
        script = content_curator.group_spots_for_reels(district, top_spots)
        video_path = video_creator.create_video(f"{district}_TOP5", script, all_image_paths)
        
        if video_path:
            await query.message.reply_video(video=open(video_path, 'rb'), caption=f"✅ {district} 릴스 영상 제작 완료!")
        else:
            await query.message.reply_text("❌ 영상 제작에 실패했습니다.")

def get_bot_app():
    app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("rank", rank))
    app.add_handler(CommandHandler("auto_scan", auto_scan))
    app.add_handler(CallbackQueryHandler(button_handler))
    return app
