from src.db.database import get_connection


class UsersRepository:

    def add(self, user_id: int):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO users (user_id)
            VALUES (?)
        """, (user_id,))

        conn.commit()
        conn.close()

    def get_all(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT user_id FROM users")
        rows = cursor.fetchall()

        conn.close()
        return [row[0] for row in rows]

    def get_settings(self, user_id: int):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT timezone, daily_summary, reminders
            FROM users
            WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return "UTC", 1, 1

        return row

    def get_timezone(self, user_id: int):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT timezone FROM users WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        return row[0] if row else "UTC"