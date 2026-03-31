import logging
import unittest
from types import SimpleNamespace

from fastapi.testclient import TestClient

from src.infrastructure.football_api_client import FootballApiError
from src.web.app import create_web_app


class FakeMatchService:
    def __init__(self):
        self.matches = [
            {
                "id": 1,
                "home": "Arsenal",
                "away": "Chelsea",
                "league_id": 39,
                "league": "Premier League",
                "country": "England",
                "date": "2026-03-31T19:00:00+00:00",
                "status": "NS",
                "status_long": "Not Started",
                "score": "-",
                "home_goals": None,
                "away_goals": None,
                "popularity_score": 100,
            },
            {
                "id": 2,
                "home": "Sevilla",
                "away": "Betis",
                "league_id": 140,
                "league": "La Liga",
                "country": "Spain",
                "date": "2026-03-31T21:00:00+00:00",
                "status": "FT",
                "status_long": "Match Finished",
                "score": "2:1",
                "home_goals": 2,
                "away_goals": 1,
                "popularity_score": 80,
            },
        ]

    async def get_today_matches(self):
        return self.matches

    async def get_live_matches(self):
        return self.matches[:1]

    async def get_upcoming_matches(self, limit: int = 10):
        return self.matches

    async def get_match(self, match_id: int):
        return next((match for match in self.matches if match["id"] == match_id), None)

    async def get_standings(self, league_query: str | None = None):
        return [
            {"rank": 1, "team": "Arsenal", "points": 76, "played": 30},
            {"rank": 2, "team": "Liverpool", "points": 74, "played": 30},
        ]

    async def get_match_events(self, match_id: int):
        return [{"minute": 10, "team": "Arsenal", "type": "Goal", "detail": "Normal Goal", "player": "Saka"}]

    async def get_match_statistics(self, match_id: int):
        return [{"team": "Arsenal", "entries": [{"type": "Shots", "value": 8}]}]

    async def get_match_lineups(self, match_id: int):
        return [{"team": "Arsenal", "formation": "4-3-3", "coach": "Coach", "start_xi": [], "substitutes": []}]

    async def get_match_players(self, match_id: int):
        return [{"team": "Arsenal", "name": "Saka", "position": "F", "rating": "8.0", "minutes": 90}]

    @staticmethod
    def filter_matches_by_league(matches: list[dict], league_id: int | None = None):
        if league_id is None:
            return matches
        return [match for match in matches if match["league_id"] == league_id]

    @staticmethod
    def supported_leagues():
        return [{"id": 39, "name": "Premier League"}, {"id": 140, "name": "La Liga"}]


class ErrorMatchService(FakeMatchService):
    async def get_live_matches(self):
        raise FootballApiError("Daily limit reached", details="requests limit")


class FakeFavoritesService:
    async def get_user_favorites_overview(self, user_id: int):
        return [
            {
                "user_id": user_id,
                "team_id": 42,
                "team_name": "Arsenal",
                "next_match": {
                    "id": 1,
                    "home": "Arsenal",
                    "away": "Chelsea",
                    "league_id": 39,
                    "league": "Premier League",
                    "country": "England",
                    "date": "2026-03-31T19:00:00+00:00",
                    "status": "NS",
                    "status_long": "Not Started",
                    "score": "-",
                    "home_goals": None,
                    "away_goals": None,
                    "popularity_score": 100,
                },
                "last_match": None,
            }
        ]


class WebAppTests(unittest.TestCase):
    def build_client(self, match_service=None):
        services = SimpleNamespace(
            logger=logging.getLogger("test"),
            match_service=match_service or FakeMatchService(),
            favorites_service=FakeFavoritesService(),
        )
        return TestClient(create_web_app(services))

    def test_today_endpoint_returns_serialized_matches(self):
        with self.build_client() as client:
            response = client.get("/api/today?league_id=39")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["matches"]), 1)
        self.assertTrue(payload["matches"][0]["home"], "Arsenal")

    def test_root_endpoint_returns_html(self):
        with self.build_client() as client:
            response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Football Match Center", response.text)

    def test_live_alias_returns_items(self):
        with self.build_client() as client:
            response = client.get("/live")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"][0]["home"], "Arsenal")
        self.assertEqual(response.json()["source"], "live")

    def test_matches_endpoint_returns_upcoming_items(self):
        with self.build_client() as client:
            response = client.get("/matches")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["items"]), 2)
        self.assertEqual(response.json()["source"], "today")

    def test_standings_endpoint_returns_league_and_items(self):
        with self.build_client() as client:
            response = client.get("/standings?league_id=39")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["league"]["id"], 39)
        self.assertEqual(payload["items"][0]["team"], "Arsenal")
        self.assertEqual(payload["source"], "api")

    def test_matches_endpoint_uses_featured_fallback_when_api_is_empty(self):
        class EmptyMatchService(FakeMatchService):
            async def get_today_matches(self):
                return []

            async def get_upcoming_matches(self, limit: int = 10):
                raise FootballApiError("No data", details="provider issue")

        with self.build_client(match_service=EmptyMatchService()) as client:
            response = client.get("/matches")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["source"], "featured")
        self.assertTrue(payload["items"])

    def test_favorites_endpoint_returns_overview(self):
        with self.build_client() as client:
            response = client.get("/api/favorites/7")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["favorites"][0]["team_name"], "Arsenal")
        self.assertEqual(payload["favorites"][0]["next_match"]["id"], 1)

    def test_favorites_alias_returns_message_without_telegram_user(self):
        with self.build_client() as client:
            response = client.get("/favorites")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["source"], "telegram-required")
        self.assertFalse(payload["items"])

    def test_favorites_alias_returns_items_when_user_id_is_present(self):
        with self.build_client() as client:
            response = client.get("/favorites?user_id=7")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["source"], "api")
        self.assertEqual(payload["items"][0]["team_name"], "Arsenal")

    def test_football_api_error_becomes_service_unavailable(self):
        with self.build_client(match_service=ErrorMatchService()) as client:
            response = client.get("/api/live")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"], "Daily limit reached")


if __name__ == "__main__":
    unittest.main()
