from src.config.settings import DEFAULT_TIMEZONE
from src.db.database import get_connection


class UsersRepository:
    def add(self, user_id: int):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO users (user_id, timezone)
            VALUES (?, ?)
            """,
            (user_id, DEFAULT_TIMEZONE),
        )
        conn.commit()
        conn.close()

    def get_all(self):
        conn = get_connection()
        cursor = conn.cursor()
        rows = cursor.execute("SELECT user_id FROM users").fetchall()
        conn.close()
        return [row["user_id"] for row in rows]

    def get_settings(self, user_id: int):
        conn = get_connection()
        cursor = conn.cursor()
        row = cursor.execute(
            """
            SELECT timezone, daily_summary, reminders
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
        conn.close()

        if not row:
            return DEFAULT_TIMEZONE, 1, 1

        return row["timezone"], row["daily_summary"], row["reminders"]

    def set_timezone(self, user_id: int, timezone: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE users
            SET timezone = ?
            WHERE user_id = ?
            """,
            (timezone, user_id),
        )
        conn.commit()
        conn.close()

    def get_timezone(self, user_id: int):
        timezone, _, _ = self.get_settings(user_id)
        return timezone

    def set_reminders_enabled(self, user_id: int, enabled: bool):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE users
            SET reminders = ?
            WHERE user_id = ?
            """,
            (1 if enabled else 0, user_id),
        )
        conn.commit()
        conn.close()
