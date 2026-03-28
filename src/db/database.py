import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "bot.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            timezone TEXT DEFAULT 'UTC',
            daily_summary INTEGER DEFAULT 1,
            reminders INTEGER DEFAULT 1
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            team_id INTEGER,
            team_name TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            match_id INTEGER NOT NULL,
            notify_time TEXT NOT NULL,
            sent INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reminder_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            fixture_id INTEGER NOT NULL,
            sent_at TEXT NOT NULL
        )
        """
    )

    _migrate_users_table(cursor)
    _ensure_column(cursor, "favorites", "team_id", "INTEGER")
    _ensure_column(cursor, "notifications", "created_at", "TEXT DEFAULT CURRENT_TIMESTAMP")

    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_favorites_user_team_name ON favorites(user_id, team_name)"
    )
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_notifications_user_match ON notifications(user_id, match_id)"
    )
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_reminder_log_user_fixture ON reminder_log(user_id, fixture_id)"
    )

    conn.commit()
    conn.close()


def _ensure_column(cursor, table_name: str, column_name: str, column_definition: str):
    columns = {
        row["name"]
        for row in cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in columns:
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        )


def _migrate_users_table(cursor):
    columns = {
        row["name"]
        for row in cursor.execute("PRAGMA table_info(users)").fetchall()
    }

    if "timezone" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN timezone TEXT DEFAULT 'UTC'")

    if "daily_summary" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN daily_summary INTEGER DEFAULT 1")
        if "daily_summary_enabled" in columns:
            cursor.execute(
                """
                UPDATE users
                SET daily_summary = COALESCE(daily_summary_enabled, 1)
                """
            )

    if "reminders" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN reminders INTEGER DEFAULT 1")
        if "reminders_enabled" in columns:
            cursor.execute(
                """
                UPDATE users
                SET reminders = COALESCE(reminders_enabled, 1)
                """
            )
