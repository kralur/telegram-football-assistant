import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "favorites.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER,
            team_id INTEGER,
            team_name TEXT,
            PRIMARY KEY (user_id, team_id)
        )
    """)


    conn.commit()
    conn.close()


def add_favorite(user_id: int, team_id: int, team_name: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO favorites (user_id, team_id, team_name) VALUES (?, ?, ?)",
        (user_id, team_id, team_name)
    )

    conn.commit()
    conn.close()


def get_favorites(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT team_id, team_name FROM favorites WHERE user_id = ?",
        (user_id,)
    )

    rows = cursor.fetchall()
    conn.close()

    return rows  # [(team_id, team_name), ...]


