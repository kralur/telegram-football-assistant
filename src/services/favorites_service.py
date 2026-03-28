class FavoritesService:
    def __init__(self, repository):
        self.repository = repository

    def add_team(self, user_id: int, team_name: str, team_id: int | None = None):
        self.repository.add(user_id, team_name=team_name, team_id=team_id)

    def remove_team(self, user_id: int, team_name: str | None = None, team_id: int | None = None):
        self.repository.remove(user_id, team_name=team_name, team_id=team_id)

    def get_user_favorites(self, user_id: int):
        return self.repository.get(user_id)
