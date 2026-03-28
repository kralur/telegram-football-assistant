from src.db.database import get_connection


class ReminderLogRepository:
    def has_record(self, user_id: int, fixture_id: int) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        row = cursor.execute(
            """
            SELECT 1
            FROM reminder_log
            WHERE user_id = ? AND fixture_id = ?
            """,
            (user_id, fixture_id),
        ).fetchone()
        conn.close()
        return row is not None

    def add_record(self, user_id: int, fixture_id: int, sent_at: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO reminder_log (user_id, fixture_id, sent_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, fixture_id) DO NOTHING
            """,
            (user_id, fixture_id, sent_at),
        )
        conn.commit()
        conn.close()
