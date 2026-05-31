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
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemma2:9b")
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    
    # Social Media (Optional)
    INSTAGRAM_USER_ID: str = os.getenv("INSTAGRAM_USER_ID", "")
    INSTAGRAM_ACCESS_TOKEN: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    
    # Paths & DB
    DB_PATH: str = str(PROJECT_ROOT / "data_storage" / "hotplace.db")
    LOG_FILE: str = str(PROJECT_ROOT / "logs" / "app.log")
    
    # Scheduler
    DAILY_CHECK_TIME: str = "10:00"

settings = Settings()

# Ensure directories
os.makedirs(os.path.dirname(settings.DB_PATH), exist_ok=True)
os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
