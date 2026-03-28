class FavoritesService:

    def __init__(self, repository):
        self.repository = repository

    # ---------- ADD ----------
    def add_team(self, user_id: int, team_name: str):
        self.repository.add(user_id, team_name)

    # ---------- REMOVE ----------
    def remove_team(self, user_id: int, team_name: str):
        self.repository.remove(user_id, team_name)

    # ---------- GET ----------
    def get_user_favorites(self, user_id: int):
        return self.repository.get(user_id)