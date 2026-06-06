import sqlite3
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "data/db/app.sqlite"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes the database schema and enables WAL mode."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 1. Enable WAL mode for better local concurrency
        cursor.execute("PRAGMA journal_mode=WAL;")
        
        # 2. Execute DDL
        schema = """
        CREATE TABLE IF NOT EXISTS batch_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT CHECK(status IN ('running', 'completed', 'failed')),
            config_json TEXT
        );

        CREATE TABLE IF NOT EXISTS style_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_post_url TEXT,
            visual_pattern_json TEXT,
            text_pattern_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS content_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_run_id INTEGER,
            style_pattern_id INTEGER,
            hook TEXT,
            body TEXT,
            cta TEXT,
            hashtags TEXT,
            status TEXT DEFAULT 'draft',
            FOREIGN KEY(batch_run_id) REFERENCES batch_runs(id)
        );

        CREATE TABLE IF NOT EXISTS render_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            draft_id INTEGER,
            file_path TEXT,
            imperfection_metadata TEXT,
            is_approved INTEGER DEFAULT 0,
            FOREIGN KEY(draft_id) REFERENCES content_drafts(id)
        );

        CREATE TABLE IF NOT EXISTS performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER,
            views INTEGER,
            saves INTEGER,
            shares INTEGER,
            retention_rate REAL,
            FOREIGN KEY(asset_id) REFERENCES render_assets(id)
        );

        CREATE INDEX IF NOT EXISTS idx_batch_status ON batch_runs(status);
        CREATE INDEX IF NOT EXISTS idx_draft_batch ON content_drafts(batch_run_id);
        """
        cursor.executescript(schema)
        conn.commit()
        conn.close()
        logger.info(f"📁 Database initialized with WAL mode at {self.db_path}")

    def execute(self, query: str, params: tuple = ()):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            last_id = cursor.lastrowid
            return last_id
        finally:
            conn.close()

    def fetch_all(self, query: str, params: tuple = ()):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

db = DatabaseManager()
