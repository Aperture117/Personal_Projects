from src.services.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)

class ContentCurator:
    def group_spots_for_reels(self, district: str, spots: list):
        """
        Creates a single, cohesive Reels script for 3-5 spots in a region.
        """
        spots_str = ", ".join([s['name'] for s in spots])
        prompt = f"""
        당신은 대한민국 최고의 소셜 미디어 성장 마케터입니다.
        이번 주제는 '{district} 반드시 가봐야 할 핫플 TOP {len(spots)}' 입니다.
        
        포함될 장소들: {spots_str}
        
        요청사항:
        1. 60초 분량의 릴스 대본을 작성해주세요.
        2. 장소별로 가장 힙한 포인트 한 가지만 짚어서 빠르게 넘어가는 구성으로 해주세요.
        3. 전체적으로 '이 영상 저장 안 하면 손해'라는 느낌을 팍팍 풍겨주세요.
        4. 오프닝에 강력한 후크(예: "{district} 갈 사람 무조건 저장하세요!")를 넣어주세요.
        """
        
        try:
            return ai_service.generate_content("reels_curation", district, prompt)
        except Exception as e:
            logger.error(f"Curation Error: {e}")
            return f"{district} 최고의 맛집 {len(spots)}곳을 소개합니다!"

content_curator = ContentCurator()
