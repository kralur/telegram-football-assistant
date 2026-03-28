import httpx
from datetime import datetime
from src.config.settings import FOOTBALL_API_KEY


class FootballApiClient:

    BASE_URL = "https://v3.football.api-sports.io"

    def __init__(self):
        if not FOOTBALL_API_KEY:
            raise ValueError("FOOTBALL_API_KEY is missing")

        self.headers = {
            "x-apisports-key": FOOTBALL_API_KEY
        }

        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.headers,
            timeout=10.0
        )

    async def _get(self, endpoint: str, params: dict):
        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    # ---------- TODAY ----------
    async def get_today_fixtures(self):
        today = datetime.utcnow().strftime("%Y-%m-%d")

        data = await self._get(
            "/fixtures",
            {
                "date": today,
                "timezone": "UTC"
            }
        )

        if not data or "response" not in data:
            return []

        return data["response"]

    # ---------- BY DATE ----------
    async def get_fixtures_by_date(self, date: str):
        data = await self._get(
            "/fixtures",
            {
                "date": date,
                "timezone": "UTC"
            }
        )

        if not data or "response" not in data:
            return []

        return data["response"]

    # ---------- SEARCH TEAM ----------
    async def search_team(self, query: str):
        data = await self._get(
            "/teams",
            {"search": query}
        )

        if not data or "response" not in data:
            return []

        return data["response"]

    # ---------- NEXT MATCHES ----------
    async def get_next_fixtures_by_team_id(self, team_id: int):
        data = await self._get(
            "/fixtures",
            {
                "team": team_id,
                "next": 5,
                "timezone": "UTC"
            }
        )

        if not data or "response" not in data:
            return []

        return data["response"]