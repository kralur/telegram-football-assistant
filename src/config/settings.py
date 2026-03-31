import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CACHE_TTL_MATCHES = int(os.getenv("CACHE_TTL_MATCHES", "300"))
CACHE_TTL_STANDINGS = int(os.getenv("CACHE_TTL_STANDINGS", "900"))
CACHE_TTL_SCORERS = int(os.getenv("CACHE_TTL_SCORERS", "900"))
CACHE_TTL_SEARCH = int(os.getenv("CACHE_TTL_SEARCH", "600"))
SCHEDULER_INTERVAL_SECONDS = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "30"))
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "UTC")
WEBAPP_HOST = os.getenv("WEBAPP_HOST", os.getenv("HOST", "0.0.0.0"))
WEBAPP_PORT = int(os.getenv("PORT", os.getenv("WEBAPP_PORT", "8000")))
APP_RUNTIME = os.getenv("APP_RUNTIME", "")
