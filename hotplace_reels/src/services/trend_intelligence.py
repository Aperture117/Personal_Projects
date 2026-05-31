import logging
from src.services.naver_service import NaverService
from src.services.trend_engine import trend_engine

logger = logging.getLogger(__name__)

class TrendIntelligenceService:
    def __init__(self):
        self.naver = NaverService()
        # List of major hot districts in Seoul/Nationwide to scan
        self.districts = [
            "성수동", "한남동", "용리단길", "연남동", "잠실", 
            "압구정", "익선동", "을지로", "서촌", "해운대", "황리단길"
        ]

    def scan_nationwide_trends(self, limit: int = 5):
        """
        Scans pre-defined districts and returns a ranked list of top trending regions.
        """
        logger.info("🌍 Scanning nationwide trends...")
        results = []
        
        for district in self.districts:
            # Check general mention volume for the district as a keyword
            counts = self.naver.get_mention_counts(f"{district} 맛집")
            results.append({
                "district": district, 
                "blog_count": counts['blog_count'],
                "news_count": counts['news_count'],
                "total_mentions": counts['blog_count'] + counts['news_count']
            })
        
        # Sort by mention volume to find today's 'Hot Regions'
        ranked = sorted(results, key=lambda x: x['total_mentions'], reverse=True)
        return ranked[:limit]

trend_intelligence = TrendIntelligenceService()
