import os
from pathlib import Path
from dotenv import load_dotenv

# ---- Определяем корень проекта ----
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ---- Явно указываем путь к .env ----
ENV_PATH = BASE_DIR / ".env"

# ---- Загружаем переменные ----
load_dotenv(dotenv_path=ENV_PATH)

# ---- Переменные окружения ----
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ---- Проверка токена ----
if not TELEGRAM_BOT_TOKEN:
    raise ValueError(
        f"TELEGRAM_BOT_TOKEN not found. Checked path: {ENV_PATH}"
    )