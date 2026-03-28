from datetime import UTC, datetime
import logging

import httpx

from src.config.settings import FOOTBALL_API_KEY


class FootballApiError(Exception):
    def __init__(self, user_message: str, *, details: str | None = None):
        super().__init__(user_message)
        self.user_message = user_message
        self.details = details or user_message


class FootballApiClient:
    BASE_URL = "https://v3.football.api-sports.io"

    def __init__(self):
        if not FOOTBALL_API_KEY:
            raise ValueError("FOOTBALL_API_KEY is missing")

        self.logger = logging.getLogger("football_bot")
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"x-apisports-key": FOOTBALL_API_KEY},
            timeout=10.0,
        )

    async def _get(self, endpoint: str, params: dict):
        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            self.logger.warning(
                "Football API returned status=%s endpoint=%s params=%s body=%s",
                exc.response.status_code,
                endpoint,
                params,
                exc.response.text[:300],
            )
            raise FootballApiError(
                "Football data provider is temporarily unavailable. Please try again later.",
                details=f"status={exc.response.status_code} endpoint={endpoint}",
            ) from exc
        except Exception as exc:
            self.logger.exception(
                "Football API request failed endpoint=%s params=%s error=%s",
                endpoint,
                params,
                exc,
            )
            raise FootballApiError(
                "Football data provider is temporarily unavailable. Please try again later.",
                details=f"endpoint={endpoint} params={params}",
            ) from exc

        errors = data.get("errors") or {}
        if errors:
            details = "; ".join(f"{key}: {value}" for key, value in errors.items() if value)
            self.logger.warning(
                "Football API returned payload errors endpoint=%s params=%s errors=%s",
                endpoint,
                params,
                details,
            )
            if "request" in details.lower() and "limit" in details.lower():
                raise FootballApiError(
                    "API request limit reached for today. Please try again later.",
                    details=details,
                )
            raise FootballApiError(
                "Football data provider returned an error. Please try again later.",
                details=details,
            )
        return data.get("response", [])

    async def get_today_fixtures(self):
        return await self.get_fixtures_by_date(datetime.now(UTC).strftime("%Y-%m-%d"))

    async def get_fixtures_by_date(self, date: str):
        return await self._get("/fixtures", {"date": date, "timezone": "UTC"})

    async def get_live_fixtures(self):
        return await self._get("/fixtures", {"live": "all", "timezone": "UTC"})

    async def get_upcoming_fixtures(self, limit: int = 10):
        return await self._get("/fixtures", {"next": limit, "timezone": "UTC"})

    async def get_standings(self, league_id: int, season: int):
        response = await self._get(
            "/standings",
            {"league": league_id, "season": season},
        )
        if not response:
            return []
        standings = response[0].get("league", {}).get("standings", [])
        return standings[0] if standings else []

    async def get_top_scorers(self, league_id: int, season: int):
        return await self._get(
            "/players/topscorers",
            {"league": league_id, "season": season},
        )

    async def search_team(self, query: str):
        return await self._get("/teams", {"search": query})

    async def get_next_fixtures_by_team_id(self, team_id: int, limit: int = 5):
        return await self._get(
            "/fixtures",
            {"team": team_id, "next": limit, "timezone": "UTC"},
        )

    async def get_fixture(self, match_id: int):
        response = await self._get("/fixtures", {"id": match_id, "timezone": "UTC"})
        return response[0] if response else None

    async def aclose(self):
        await self.client.aclose()
