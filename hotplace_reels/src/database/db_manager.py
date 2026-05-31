import sqlite3
import polars as pl
from datetime import datetime
from src.core.config import settings

class DBManager:
    def __init__(self):
        self.db_path = settings.DB_PATH
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            # Places table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS places (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    address TEXT,
                    category TEXT,
                    discovery_date DATETIME
                )
            """)
            # Trends table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    place_id INTEGER,
                    blog_count INTEGER,
                    news_count INTEGER,
                    captured_at DATETIME,
                    FOREIGN KEY(place_id) REFERENCES places(id)
                )
            """)
            # Content Queue table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS content_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    place_name TEXT,
                    content_type TEXT,
                    payload TEXT,
                    status TEXT DEFAULT 'PENDING',
                    created_at DATETIME,
                    approved_at DATETIME
                )
            """)

    def save_trend(self, name, address, category, blog_count, news_count):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO places (name, address, category, discovery_date) VALUES (?, ?, ?, ?)",
                           (name, address, category, datetime.now()))
            cursor.execute("SELECT id FROM places WHERE name = ?", (name,))
            place_id = cursor.fetchone()[0]
            
            conn.execute("INSERT INTO trends (place_id, blog_count, news_count, captured_at) VALUES (?, ?, ?, ?)",
                         (place_id, blog_count, news_count, datetime.now()))

    def get_latest_trends(self, district: str = None) -> pl.DataFrame:
        query = """
            SELECT p.name, p.category, p.address, t.blog_count, t.news_count, t.captured_at
            FROM places p
            JOIN trends t ON p.id = t.place_id
            WHERE t.id IN (SELECT MAX(id) FROM trends GROUP BY place_id)
        """
        if district:
            query += f" AND (p.name LIKE '%{district}%' OR p.address LIKE '%{district}%')"
            
        with sqlite3.connect(self.db_path) as conn:
            return pl.read_database(query, conn)

    def add_to_queue(self, place_name, content_type, payload):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO content_queue (place_name, content_type, payload, created_at)
                VALUES (?, ?, ?, ?)
            """, (place_name, content_type, payload, datetime.now()))
            return True

db = DBManager()
