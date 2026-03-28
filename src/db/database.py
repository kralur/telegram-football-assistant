import sqlite3
from pathlib import Path

# ---- Путь к базе ----
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "bot.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # ---------- USERS ----------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            timezone TEXT DEFAULT 'UTC',
            daily_summary INTEGER DEFAULT 1,
            reminders INTEGER DEFAULT 1
        )
    """)

    # ---------- FAVORITES ----------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            team_name TEXT
        )
    """)

    # ---------- REMINDER LOG ----------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminder_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            fixture_id INTEGER,
            sent_at TEXT
        )
    """)

    conn.commit()
    conn.close()