import logging
import json
from src.services.ai_service import ai_service
from src.database.db_manager import db
from src.core.config import settings

logger = logging.getLogger(__name__)

class ContentGeneratorAgent:
    """
    Sub-Agent: Generates human-like drafts based on Style DNA.
    """
    async def create_draft(self, batch_id: int, style_pattern: dict):
        logger.info(f"🎨 ContentGen: Drafting content using style pattern {style_pattern.get('id')}...")
        
        niche = style_pattern.get("niche", "Daily Life")
        
        prompt = f"""
        당신은 SNS를 즐겨하는 20대 한국인 인플루언서입니다.
        아래 [스타일 가이드]를 완벽히 준수하여 '{niche}'에 대한 콘텐츠를 작성하세요.
        
        [스타일 가이드]:
        - 비공식성 수준: {style_pattern.get('text_informality', 0.8)}
        - 사용 어투: {style_pattern.get('slang_used', ['~네여', '~함', '대박'])}
        - 이모지 전략: {style_pattern.get('emoji_strategy', '문장 중간 삽입')}
        
        [수행 규칙]:
        1. 문어체 절대 금지. 날것의 구어체만 사용.
        2. 오타를 한두 개 섞어주세요.
        3. 문장은 짧고 간결하게 '의식의 흐름'대로 쓰세요.
        
        결과를 JSON으로 출력하세요:
        {{
          "hook": "첫 문장 (충격적이거나 궁금증 유발)",
          "body": "본문 내용 (꿀팁 또는 정보)",
          "cta": "마지막 한마디 (님들 생각은?)",
          "hashtags": "해시태그 10개"
        }}
        """
        
        try:
            response = ai_service.client.generate(model=settings.LLM_MODEL, prompt=prompt, format="json")
            draft_data = json.loads(response['response'])

            # --- 🛠️ Nuclear Fix: Force everything to strings for SQLite ---
            def to_str(val):
                if isinstance(val, list): return " ".join([str(x) for x in val])
                return str(val) if val is not None else ""

            clean_hook = to_str(draft_data.get('hook', ''))
            clean_body = to_str(draft_data.get('body', ''))
            clean_cta = to_str(draft_data.get('cta', ''))
            clean_hashtags = to_str(draft_data.get('hashtags', ''))

            # Save to content_drafts table
            draft_id = db.execute(
                """INSERT INTO content_drafts (batch_run_id, style_pattern_id, hook, body, cta, hashtags) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (batch_id, style_pattern.get('id'), clean_hook, clean_body, clean_cta, clean_hashtags)
            )

            draft_data['id'] = draft_id
            return draft_data
        except Exception as e:
            logger.error(f"Content Generation failed: {e}")
            return None

content_generator = ContentGeneratorAgent()
