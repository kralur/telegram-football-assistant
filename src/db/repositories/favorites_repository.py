from src.db.database import get_connection


class FavoritesRepository:

    def add(self, user_id: int, team_name: str):
        conn = get_connection()
        cursor = conn.cursor()

        # Проверяем, нет ли уже такой команды
        cursor.execute("""
            SELECT id FROM favorites
            WHERE user_id = ? AND team_name = ?
        """, (user_id, team_name))

        exists = cursor.fetchone()

        if not exists:
            cursor.execute("""
                INSERT INTO favorites (user_id, team_name)
                VALUES (?, ?)
            """, (user_id, team_name))

        conn.commit()
        conn.close()

    def remove(self, user_id: int, team_name: str):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM favorites
            WHERE user_id = ? AND team_name = ?
        """, (user_id, team_name))

        conn.commit()
        conn.close()

    def get(self, user_id: int):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT team_name FROM favorites
            WHERE user_id = ?
        """, (user_id,))

        rows = cursor.fetchall()
        conn.close()

        return [row[0] for row in rows]