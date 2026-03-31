import unittest

from src.services.favorites_service import FavoritesService


class FakeFavoritesRepository:
    def __init__(self):
        self.rows = {}

    def add(self, user_id: int, team_name: str, team_id: int | None = None):
        current = self.rows.setdefault(user_id, [])
        for team in current:
            if team["team_name"] == team_name:
                team["team_id"] = team_id
                return
        current.append({"user_id": user_id, "team_name": team_name, "team_id": team_id})

    def remove(self, user_id: int, team_name: str | None = None, team_id: int | None = None):
        current = self.rows.get(user_id, [])
        self.rows[user_id] = [
            team
            for team in current
            if not (
                (team_name is not None and team["team_name"] == team_name)
                or (team_id is not None and team["team_id"] == team_id)
            )
        ]

    def get(self, user_id: int):
        return list(self.rows.get(user_id, []))


class FakeMatchService:
    async def search_team(self, query: str):
        return [{"team": {"id": 77, "name": query}}]

    async def get_team_matches(self, team_id: int, limit: int = 1):
        return [
            {
                "id": 101,
                "home": "Arsenal",
                "away": "Chelsea",
                "date": "2026-03-31T18:00:00+00:00",
                "score": "-",
            }
        ]

    async def get_last_team_matches(self, team_id: int, limit: int = 1):
        return [
            {
                "id": 88,
                "home": "Liverpool",
                "away": "Arsenal",
                "date": "2026-03-28T18:00:00+00:00",
                "score": "2:1",
            }
        ]


class FavoritesServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.repository = FakeFavoritesRepository()
        self.match_service = FakeMatchService()
        self.service = FavoritesService(self.repository, self.match_service)

    async def test_get_user_favorites_overview_adds_next_and_last_match(self):
        self.repository.add(1, "Arsenal", team_id=77)

        overview = await self.service.get_user_favorites_overview(1)

        self.assertEqual(overview[0]["next_match"]["id"], 101)
        self.assertEqual(overview[0]["last_match"]["score"], "2:1")

    async def test_get_user_favorites_overview_resolves_missing_team_id(self):
        self.repository.add(1, "Arsenal", team_id=None)

        overview = await self.service.get_user_favorites_overview(1)

        self.assertEqual(overview[0]["team_id"], 77)
        self.assertEqual(self.repository.get(1)[0]["team_id"], 77)


if __name__ == "__main__":
    unittest.main()
