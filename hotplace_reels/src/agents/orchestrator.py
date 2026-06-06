import logging
import asyncio
import json
import time
from src.database.db_manager import db
from src.agents.trend_scout import trend_scout
from src.agents.human_style_ref import human_style_ref
from src.agents.content_gen import content_generator
from src.agents.render_agent import render_agent
from src.agents.quality_scorer import quality_scorer
from src.services.messaging_service import send_approval_message
from src.services.status_service import send_status_update

logger = logging.getLogger(__name__)

class BatchOrchestrator:
    """
    👑 The Central OS: Manages the full lifecycle of an autonomous content batch with Smart Retries.
    """
    async def run_batch(self, niche: str = None):
        logger.info("🎬 [Batch OS] Starting new production cycle...")
        await send_status_update(f"배치 가동 시작 (주제: {niche or 'Global Trend'})")
        
        batch_id = db.execute(
            "INSERT INTO batch_runs (status, config_json) VALUES (?, ?)",
            ("running", json.dumps({"niche": niche}))
        )

        try:
            # 1. TREND & STYLE PHASE
            await send_status_update("🕵️ 실시간 트렌드 및 인간의 날것 패턴 분석 중...")
            raw_trends = await trend_scout.run_discovery(niche)
            style_patterns = await human_style_ref.analyze_viral_patterns(raw_trends)
            
            if not style_patterns:
                await send_status_update("❌ 스타일 패턴 추출 실패. 배치를 중단합니다.")
                raise Exception("Failed to extract style patterns.")

            # 2. PRODUCTION PHASE (with Smart Retries)
            for p_idx, pattern in enumerate(style_patterns):
                await send_status_update(f"🎨 {p_idx+1}번 스타일 기반 콘텐츠 제작 시작...")
                
                success = False
                for attempt in range(3): # Max 3 Retries per pattern
                    # Generate & Render
                    draft = await content_generator.create_draft(batch_id, pattern)
                    if not draft: continue

                    assets = await render_agent.render_imperfect_asset(draft, pattern)

                    # Quality Control
                    evaluation = quality_scorer.evaluate(assets, draft)
                    score = evaluation['score']

                    if evaluation["is_high_quality"]:
                        await send_status_update(f"✅ 고품질 콘텐츠 생성 성공! (점수: {score:.2f})")
                        summary = f"🔥 Score: {score:.2f}\nTopic: {niche or 'Trending'}"
                        await send_approval_message(assets, summary)
                        success = True
                        break
                    else:
                        await send_status_update(f"🔄 퀄리티 저하(점수: {score:.2f})로 인한 재시도 중... ({attempt+1}/3)")
                        logger.warning(f"⚠️ Low-quality (Score: {score:.2f}). Attempt {attempt+1} failed.")

                if not success:
                    await send_status_update(f"🚫 {p_idx+1}번 스타일은 3회 시도 후에도 퀄리티 미달(최종 점수: {score:.2f})로 폐기되었습니다.")

            # 3. Finalize Batch
            db.execute("UPDATE batch_runs SET status='completed' WHERE id=?", (batch_id,))
            await send_status_update("🏁 전체 배치 사이클이 완료되었습니다.")
            logger.info(f"🏁 [Batch OS] Cycle #{batch_id} complete.")

        except Exception as e:
            db.execute("UPDATE batch_runs SET status='failed' WHERE id=?", (batch_id,))
            await send_status_update(f"💥 배치 실행 중 치명적 오류 발생: {str(e)}")
            logger.error(f"💥 [Batch OS] Batch #{batch_id} FAILED: {e}")
            return {"error": str(e)}

batch_orchestrator = BatchOrchestrator()
