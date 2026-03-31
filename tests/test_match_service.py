import unittest
from datetime import UTC, datetime

from src.services.match_service import MatchService
from src.services.search_service import SearchService
from src.infrastructure.football_api_client import FootballApiError


class FakeCache:
    def __init__(self):
        self.storage = {}

    def get(self, key):
        return self.storage.get(key)

    def set(self, key, value, ttl: int):
        self.storage[key] = value


class FakeApiClient:
    def __init__(self):
        self.today_calls = 0
        self.fixture_calls = 0
        self.team_search_calls = 0
        self.next_calls = 0
        self.standings_calls = []
        self.scorers_calls = []

    async def get_today_fixtures(self):
        self.today_calls += 1
        return [
            {
                "fixture": {
                    "id": 11,
                    "date": "2026-03-28T15:00:00+00:00",
                    "status": {"short": "NS", "long": "Not Started"},
                },
                "teams": {
                    "home": {"name": "Arsenal"},
                    "away": {"name": "Chelsea"},
                },
                "league": {"id": 39, "name": "Premier League"},
                "goals": {"home": None, "away": None},
            },
            {
                "fixture": {
                    "id": 12,
                    "date": "2026-03-28T18:00:00+00:00",
                    "status": {"short": "NS", "long": "Not Started"},
                },
                "teams": {
                    "home": {"name": "Brest"},
                    "away": {"name": "Reims"},
                },
                "league": {"id": 999, "name": "Unknown league"},
                "goals": {"home": None, "away": None},
            }
        ]

    async def get_live_fixtures(self):
        return []

    async def get_upcoming_fixtures(self, limit: int = 10):
        return []

    async def get_standings(self, league_id: int, season: int):
        self.standings_calls.append(season)
        if season > 2024:
            raise FootballApiError(
                "Football data provider returned an error. Please try again later.",
                details="plan: Free plans do not have access to this season, try from 2022 to 2024.",
            )
        return [
            {
                "rank": 1,
                "team": {"name": "Liverpool"},
                "points": 72,
                "all": {"played": 30},
            }
        ]

    async def get_top_scorers(self, league_id: int, season: int):
        self.scorers_calls.append(season)
        if season > 2024:
            raise FootballApiError(
                "Football data provider returned an error. Please try again later.",
                details="plan: Free plans do not have access to this season, try from 2022 to 2024.",
            )
        return [
            {
                "player": {"name": "Erling Haaland"},
                "statistics": [
                    {
                        "team": {"name": "Manchester City"},
                        "goals": {"total": 24},
                    }
                ],
            }
        ]

    async def get_fixture(self, match_id: int):
        self.fixture_calls += 1
        return {
            "fixture": {
                "id": match_id,
                "date": "2026-03-30T18:00:00+00:00",
                "status": {"short": "NS", "long": "Not Started"},
            },
            "teams": {
                "home": {"name": "Real Madrid"},
                "away": {"name": "Barcelona"},
            },
            "league": {"id": 140, "name": "La Liga"},
            "goals": {"home": None, "away": None},
        }

    async def search_team(self, query: str):
        self.team_search_calls += 1
        return [
            {"team": {"id": 1, "name": query}, "country": "England"},
        ]

    async def get_next_fixtures_by_team_id(self, team_id: int, limit: int = 5):
        self.next_calls += 1
        raise FootballApiError(
            "Football data provider returned an error. Please try again later.",
            details="plan: Free plans do not have access to the Next parameter.",
        )

    async def get_last_fixtures_by_team_id(self, team_id: int, limit: int = 5):
        raise FootballApiError(
            "Football data provider returned an error. Please try again later.",
            details="plan: Free plans do not have access to the Last parameter.",
        )

    async def get_fixtures_by_team_and_season(self, team_id: int, season: int):
        return [
            {
                "fixture": {
                    "id": 21,
                    "date": "2026-04-02T15:00:00+00:00",
                    "status": {"short": "NS", "long": "Not Started"},
                },
                "teams": {
                    "home": {"name": "Arsenal"},
                    "away": {"name": "Chelsea"},
                },
                "league": {"id": 39, "name": "Premier League"},
                "goals": {"home": None, "away": None},
            },
            {
                "fixture": {
                    "id": 22,
                    "date": "2026-03-20T15:00:00+00:00",
                    "status": {"short": "FT", "long": "Match Finished"},
                },
                "teams": {
                    "home": {"name": "Liverpool"},
                    "away": {"name": "Arsenal"},
                },
                "league": {"id": 39, "name": "Premier League"},
                "goals": {"home": 2, "away": 1},
            },
        ]


class MatchServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.api = FakeApiClient()
        self.cache = FakeCache()
        self.service = MatchService(self.api, self.cache)
        self.search_service = SearchService(self.service, self.cache)

    async def test_get_today_matches_normalizes_and_caches(self):
        first = await self.service.get_today_matches()
        second = await self.service.get_today_matches()

        self.assertEqual(self.api.today_calls, 1)
        self.assertEqual(first[0]["home"], "Arsenal")
        self.assertEqual(second[0]["score"], "-")
        self.assertEqual(len(first), 2)
        self.assertEqual(first[1]["home"], "Brest")

    async def test_get_match_caches_fixture(self):
        first = await self.service.get_match(99)
        second = await self.service.get_match(99)

        self.assertEqual(self.api.fixture_calls, 1)
        self.assertEqual(first["away"], "Barcelona")
        self.assertEqual(second["id"], 99)

    async def test_get_standings_normalizes_rows(self):
        table = await self.service.get_standings("premier league")
        self.assertEqual(table[0]["team"], "Liverpool")
        self.assertEqual(table[0]["played"], 30)
        self.assertEqual(self.api.standings_calls, [2024])

    async def test_get_top_scorers_normalizes_rows(self):
        scorers = await self.service.get_top_scorers("premier league")
        self.assertEqual(scorers[0]["player"], "Erling Haaland")
        self.assertEqual(scorers[0]["goals"], 24)
        self.assertEqual(self.api.scorers_calls, [2024])

    async def test_search_service_normalizes_and_caches(self):
        first = await self.search_service.search_teams("Arsenal")
        second = await self.search_service.search_teams("Arsenal")

        self.assertEqual(self.api.team_search_calls, 1)
        self.assertEqual(first[0]["name"], "Arsenal")
        self.assertEqual(second[0]["country"], "England")

    async def test_search_service_uses_fallback_catalog_for_partial_queries(self):
        self.api.team_search_calls = 0

        async def empty_search(query: str):
            return []

        self.api.search_team = empty_search
        results = await self.search_service.search_teams("real")

        self.assertTrue(any(team["name"] == "Real Madrid" for team in results))

    async def test_filter_matches_by_league_keeps_only_requested_league(self):
        matches = await self.service.get_today_matches()

        filtered = self.service.filter_matches_by_league(matches, league_id=39)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["home"], "Arsenal")

    async def test_get_team_matches_falls_back_when_next_is_not_available(self):
        matches = await self.service.get_team_matches(team_id=77, limit=1)

        self.assertEqual(self.api.next_calls, 1)
        self.assertEqual(matches[0]["id"], 21)

    async def test_get_last_team_matches_falls_back_when_last_is_not_available(self):
        matches = await self.service.get_last_team_matches(team_id=77, limit=1)

        self.assertEqual(matches[0]["id"], 22)

    def test_current_season_uses_start_year(self):
        self.assertEqual(self.service.get_current_season(datetime(2026, 3, 28, tzinfo=UTC)), 2025)
        self.assertEqual(self.service.get_current_season(datetime(2026, 8, 1, tzinfo=UTC)), 2026)


if __name__ == "__main__":
    unittest.main()
