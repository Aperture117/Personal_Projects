import polars as pl
from src.services.naver_service import NaverService
from src.database.db_manager import db
from sklearn.linear_model import LinearRegression
import numpy as np

class TrendEngine:
    def __init__(self):
        self.naver = NaverService()

    def discover_and_save(self, keyword: str):
        local_spots = self.naver.search_local(keyword)
        for spot in local_spots:
            name = spot.title.replace("<b>", "").replace("</b>", "")
            counts = self.naver.get_mention_counts(name)
            db.save_trend(name, spot.roadAddress, spot.category, 
                         counts['blog_count'], counts['news_count'])
        return len(local_spots)

    def get_rankings(self, district: str = None) -> pl.DataFrame:
        df = db.get_latest_trends(district=district)
        if df.is_empty(): return df
        
        # Scoring
        df = df.with_columns([
            ((pl.col("blog_count") * 0.7) + (pl.col("news_count") * 0.3)).alias("score")
        ])
        return df.sort("score", descending=True)

    def predict_future(self, name: str) -> dict:
        # Simplified prediction for the example
        # In production, we query historical trends for this name
        return {"next_week": "+15%", "next_month": "+45%"}

trend_engine = TrendEngine()
