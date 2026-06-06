import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # API Keys
    NAVER_CLIENT_ID: str = os.getenv("NAVER_CLIENT_ID", "")
    NAVER_CLIENT_SECRET: str = os.getenv("NAVER_CLIENT_SECRET", "")
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    ALLOWED_TELEGRAM_USER_IDS: str = os.getenv("ALLOWED_TELEGRAM_USER_IDS", "")
    
    # LLM
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemma2:2b")
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    # Social Media
    INSTAGRAM_USER_ID: str = os.getenv("INSTAGRAM_USER_ID", "")
    INSTAGRAM_ACCESS_TOKEN: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    
    # Paths (New Batch OS Structure)
    DATA_ROOT: Path = PROJECT_ROOT / "data"
    DB_PATH: str = str(DATA_ROOT / "db" / "app.sqlite")
    CACHE_DIR: str = str(DATA_ROOT / "cache")
    RAW_DATA_DIR: str = str(DATA_ROOT / "raw")
    DRAFTS_DIR: str = str(DATA_ROOT / "drafts")
    RENDERS_DIR: str = str(DATA_ROOT / "renders")
    LOGS_DIR: str = str(DATA_ROOT / "logs")
    
    # Scheduler
    BATCH_INTERVAL_HOURS: int = 3

settings = Settings()

# Ensure critical directories exist
for path in [settings.DB_PATH, settings.LOGS_DIR]:
    os.makedirs(os.path.dirname(path), exist_ok=True)
