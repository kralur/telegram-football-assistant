from src.db.database import get_connection


class FavoritesRepository:
    def add(self, user_id: int, team_name: str, team_id: int | None = None):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO favorites (user_id, team_id, team_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, team_name) DO UPDATE SET team_id = excluded.team_id
            """,
            (user_id, team_id, team_name),
        )
        conn.commit()
        conn.close()

    def remove(self, user_id: int, team_name: str | None = None, team_id: int | None = None):
        conn = get_connection()
        cursor = conn.cursor()

        if team_id is not None:
            cursor.execute(
                "DELETE FROM favorites WHERE user_id = ? AND team_id = ?",
                (user_id, team_id),
            )
        elif team_name is not None:
            cursor.execute(
                "DELETE FROM favorites WHERE user_id = ? AND team_name = ?",
                (user_id, team_name),
            )

        conn.commit()
        conn.close()

    def get(self, user_id: int):
        conn = get_connection()
        cursor = conn.cursor()
        rows = cursor.execute(
            """
            SELECT user_id, team_id, team_name
            FROM favorites
            WHERE user_id = ?
            ORDER BY team_name
            """,
            (user_id,),
        ).fetchall()
        conn.close()

        return [
            {
                "user_id": row["user_id"],
                "team_id": row["team_id"],
                "team_name": row["team_name"],
            }
            for row in rows
        ]
