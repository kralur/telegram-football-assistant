class FavoritesService:
    def __init__(self, repository, match_service):
        self.repository = repository
        self.match_service = match_service

    def add_team(self, user_id: int, team_name: str, team_id: int | None = None):
        self.repository.add(user_id, team_name=team_name, team_id=team_id)

    def remove_team(self, user_id: int, team_name: str | None = None, team_id: int | None = None):
        self.repository.remove(user_id, team_name=team_name, team_id=team_id)

    def get_user_favorites(self, user_id: int):
        return self.repository.get(user_id)

    async def get_user_favorites_overview(self, user_id: int):
        favorites = self.repository.get(user_id)
        overview = []

        for favorite in favorites:
            team_id = favorite.get("team_id")
            if team_id is None:
                raw_results = await self.match_service.search_team(favorite["team_name"])
                if raw_results:
                    team_id = raw_results[0].get("team", {}).get("id")
                    if team_id is not None:
                        self.repository.add(
                            user_id,
                            team_name=favorite["team_name"],
                            team_id=team_id,
                        )

            next_match = None
            last_match = None
            if team_id is not None:
                next_matches = await self.match_service.get_team_matches(team_id, limit=1)
                last_matches = await self.match_service.get_last_team_matches(team_id, limit=1)
                next_match = next_matches[0] if next_matches else None
                last_match = last_matches[0] if last_matches else None

            overview.append(
                {
                    **favorite,
                    "team_id": team_id,
                    "next_match": next_match,
                    "last_match": last_match,
                }
            )

        return overview
