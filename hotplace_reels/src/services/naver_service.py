import requests
from typing import List, Dict, Any
from pydantic import BaseModel
from src.core.config import settings

class NaverLocalResult(BaseModel):
    title: str
    link: str
    category: str
    roadAddress: str

class NaverService:
    BASE_URL = "https://openapi.naver.com/v1/search"

    def __init__(self):
        self.headers = {
            "X-Naver-Client-Id": settings.NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": settings.NAVER_CLIENT_SECRET
        }

    def _get(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not settings.NAVER_CLIENT_ID or not settings.NAVER_CLIENT_SECRET:
            return {"items": []}
        response = requests.get(f"{self.BASE_URL}/{endpoint}", headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def search_local(self, query: str, display: int = 10) -> List[NaverLocalResult]:
        data = self._get("local.json", {"query": query, "display": display})
        return [NaverLocalResult(**item) for item in data.get("items", [])]

    def search_images(self, query: str, display: int = 5) -> List[str]:
        """
        Searches for high-quality images and returns direct links.
        """
        # Improved query for better aesthetic results
        search_query = f"{query} 맛집 감성"
        data = self._get("image", {"query": search_query, "display": display, "sort": "sim", "filter": "large"})
        return [item['link'] for item in data.get("items", [])]

    def get_place_details(self, query: str) -> Dict[str, Any]:
        """
        Get rich metadata for a place to display on cards.
        """
        data = self._get("local.json", {"query": query, "display": 1})
        items = data.get("items", [])
        if items:
            item = items[0]
            return {
                "name": item['title'].replace("<b>", "").replace("</b>", ""),
                "category": item['category'],
                "address": item['roadAddress'],
                "description": f"📍 {item['roadAddress']}\n⭐ 인기 핫플레이스"
            }
        return {"name": query, "category": "Place", "address": "", "description": "인기 핫플레이스"}

    def get_mention_counts(self, query: str) -> Dict[str, int]:
        blog_data = self._get("blog.json", {"query": query, "display": 1})
        news_data = self._get("news.json", {"query": query, "display": 1})
        return {
            "blog_count": blog_data.get("total", 0),
            "news_count": news_data.get("total", 0)
        }
