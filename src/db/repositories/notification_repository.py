from src.db.database import get_connection


class NotificationRepository:
    def upsert_notification(self, user_id: int, match_id: int, notify_time: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO notifications (user_id, match_id, notify_time, sent)
            VALUES (?, ?, ?, 0)
            ON CONFLICT(user_id, match_id)
            DO UPDATE SET notify_time = excluded.notify_time, sent = 0
            """,
            (user_id, match_id, notify_time),
        )
        conn.commit()
        conn.close()

    def get_due_notifications(self, now_iso: str):
        conn = get_connection()
        cursor = conn.cursor()
        rows = cursor.execute(
            """
            SELECT id, user_id, match_id, notify_time, sent
            FROM notifications
            WHERE notify_time <= ? AND sent = 0
            ORDER BY notify_time
            """,
            (now_iso,),
        ).fetchall()
        conn.close()

        return [
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "match_id": row["match_id"],
                "notify_time": row["notify_time"],
                "sent": row["sent"],
            }
            for row in rows
        ]

    def mark_sent(self, notification_id: int):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE notifications
            SET sent = 1
            WHERE id = ?
            """,
            (notification_id,),
        )
        conn.commit()
        conn.close()

    def list_pending_for_user(self, user_id: int):
        conn = get_connection()
        cursor = conn.cursor()
        rows = cursor.execute(
            """
            SELECT id, user_id, match_id, notify_time, sent
            FROM notifications
            WHERE user_id = ? AND sent = 0
            ORDER BY notify_time
            """,
            (user_id,),
        ).fetchall()
        conn.close()

        return [
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "match_id": row["match_id"],
                "notify_time": row["notify_time"],
                "sent": row["sent"],
            }
            for row in rows
        ]
