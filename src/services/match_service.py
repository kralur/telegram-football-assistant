import uuid
from datetime import UTC, datetime, timedelta
import logging

from src.config.settings import (
    CACHE_TTL_MATCHES,
    CACHE_TTL_SCORERS,
    CACHE_TTL_STANDINGS,
)
from src.infrastructure.football_api_client import FootballApiError

POPULAR_LEAGUES = {
    "premier league": {"id": 39, "name": "Premier League"},
    "epl": {"id": 39, "name": "Premier League"},
    "la liga": {"id": 140, "name": "La Liga"},
    "laliga": {"id": 140, "name": "La Liga"},
    "serie a": {"id": 135, "name": "Serie A"},
    "bundesliga": {"id": 78, "name": "Bundesliga"},
    "ligue 1": {"id": 61, "name": "Ligue 1"},
    "champions league": {"id": 2, "name": "UEFA Champions League"},
    "ucl": {"id": 2, "name": "UEFA Champions League"},
}

LEAGUE_POPULARITY = {
    39: 100,
    2: 95,
    140: 90,
    135: 80,
    78: 80,
    61: 70,
}

TEAM_POPULARITY = {
    "Real Madrid": 50,
    "Barcelona": 50,
    "Manchester City": 45,
    "Manchester United": 45,
    "Liverpool": 45,
    "Arsenal": 42,
    "Chelsea": 40,
    "Tottenham": 35,
    "Bayern Munich": 45,
    "Borussia Dortmund": 35,
    "Juventus": 40,
    "Inter": 38,
    "Milan": 38,
    "PSG": 42,
    "Atletico Madrid": 35,
}


class MatchService:
    def __init__(self, api_client, cache):
        self.api_client = api_client
        self.cache = cache
        self._match_cache = {}
        self.logger = logging.getLogger("football_bot")

    async def get_today_matches(self):
        matches = await self._get_or_cache(
            "matches:today",
            self.api_client.get_today_fixtures,
            self._normalize_fixtures,
            CACHE_TTL_MATCHES,
        )
        return self._sort_by_popularity(matches)

    @staticmethod
    def filter_matches_by_league(matches: list[dict], league_id: int | None = None):
        if league_id is None:
            return matches
        return [match for match in matches if match.get("league_id") == league_id]

    async def get_live_matches(self):
        return await self._get_or_cache(
            "matches:live",
            self.api_client.get_live_fixtures,
            self._normalize_fixtures,
            60,
        )

    async def get_upcoming_matches(self, limit: int = 10):
        cache_key = f"matches:upcoming:{limit}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            matches = self._normalize_fixtures(
                await self.api_client.get_upcoming_fixtures(limit=limit)
            )
        except FootballApiError as exc:
            if "Next parameter" not in exc.details:
                raise
            matches = await self._fallback_upcoming_matches(limit=limit)

        self.cache.set(cache_key, matches, ttl=CACHE_TTL_MATCHES)
        return matches

    async def get_standings(self, league_query: str | None = None):
        league = self.resolve_league(league_query)
        return await self._get_league_table_data(
            cache_prefix="standings",
            loader=lambda season: self.api_client.get_standings(league["id"], season),
            normalizer=self._normalize_standings,
            league_id=league["id"],
            ttl=CACHE_TTL_STANDINGS,
        )

    async def get_top_scorers(self, league_query: str | None = None):
        league = self.resolve_league(league_query)
        return await self._get_league_table_data(
            cache_prefix="scorers",
            loader=lambda season: self.api_client.get_top_scorers(league["id"], season),
            normalizer=self._normalize_scorers,
            league_id=league["id"],
            ttl=CACHE_TTL_SCORERS,
        )

    async def get_match(self, match_id: int):
        cache_key = f"match:{match_id}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        raw_match = await self.api_client.get_fixture(match_id)
        match = self._normalize_fixture(raw_match) if raw_match else None
        if match:
            self.cache.set(cache_key, match, ttl=CACHE_TTL_MATCHES)
        return match

    async def get_match_events(self, match_id: int):
        return await self._get_or_cache(
            f"match:events:{match_id}",
            lambda: self.api_client.get_fixture_events(match_id),
            self._normalize_events,
            60,
        )

    async def get_match_statistics(self, match_id: int):
        return await self._get_or_cache(
            f"match:statistics:{match_id}",
            lambda: self.api_client.get_fixture_statistics(match_id),
            self._normalize_statistics,
            60,
        )

    async def get_match_lineups(self, match_id: int):
        return await self._get_or_cache(
            f"match:lineups:{match_id}",
            lambda: self.api_client.get_fixture_lineups(match_id),
            self._normalize_lineups,
            300,
        )

    async def get_match_players(self, match_id: int):
        return await self._get_or_cache(
            f"match:players:{match_id}",
            lambda: self.api_client.get_fixture_players(match_id),
            self._normalize_players,
            60,
        )

    async def search_team(self, query: str):
        return await self.api_client.search_team(query)

    async def get_team_matches(self, team_id: int, limit: int = 5):
        cache_key = f"matches:team:{team_id}:{limit}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            raw_matches = await self.api_client.get_next_fixtures_by_team_id(team_id, limit=limit)
            matches = self._normalize_fixtures(raw_matches)
        except FootballApiError as exc:
            if "Next parameter" not in exc.details:
                raise
            matches = await self._fallback_team_matches(team_id, limit=limit, direction="next")
        self.cache.set(cache_key, matches, ttl=CACHE_TTL_MATCHES)
        return matches

    async def get_last_team_matches(self, team_id: int, limit: int = 5):
        cache_key = f"matches:team:last:{team_id}:{limit}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            raw_matches = await self.api_client.get_last_fixtures_by_team_id(team_id, limit=limit)
            matches = self._normalize_fixtures(raw_matches)
        except FootballApiError:
            matches = await self._fallback_team_matches(team_id, limit=limit, direction="last")
        self.cache.set(cache_key, matches, ttl=CACHE_TTL_MATCHES)
        return matches

    def cache_match(self, match_data: dict):
        match_id = str(uuid.uuid4())[:8]
        self._match_cache[match_id] = match_data
        return match_id

    def get_cached_match(self, match_id: str):
        return self._match_cache.get(match_id)

    @staticmethod
    def resolve_league(league_query: str | None):
        if not league_query:
            return POPULAR_LEAGUES["premier league"]

        normalized = " ".join(league_query.lower().split())
        return POPULAR_LEAGUES.get(normalized, POPULAR_LEAGUES["premier league"])

    @staticmethod
    def supported_leagues():
        return [
            POPULAR_LEAGUES["premier league"],
            POPULAR_LEAGUES["la liga"],
            POPULAR_LEAGUES["serie a"],
            POPULAR_LEAGUES["bundesliga"],
            POPULAR_LEAGUES["ligue 1"],
            POPULAR_LEAGUES["champions league"],
        ]

    @staticmethod
    def get_current_season(now: datetime | None = None) -> int:
        now = now or datetime.now(UTC)
        return now.year - 1 if now.month < 7 else now.year

    async def _get_or_cache(self, cache_key: str, loader, normalizer, ttl: int):
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        raw_data = await loader()
        normalized = normalizer(raw_data)
        self.cache.set(cache_key, normalized, ttl=ttl)
        return normalized

    async def _get_league_table_data(self, cache_prefix: str, loader, normalizer, league_id: int, ttl: int):
        seasons_to_try = self._supported_seasons_for_plan()
        last_exc = None

        for season in seasons_to_try:
            cache_key = f"{cache_prefix}:{league_id}:{season}"
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

            try:
                raw_data = await loader(season)
            except FootballApiError as exc:
                last_exc = exc
                self.logger.info(
                    "Falling back to older season for %s league=%s after error: %s",
                    cache_prefix,
                    league_id,
                    exc.details,
                )
                continue

            normalized = normalizer(raw_data)
            self.cache.set(cache_key, normalized, ttl=ttl)
            return normalized

        if last_exc:
            raise last_exc
        return []

    async def _fallback_team_matches(self, team_id: int, limit: int, direction: str):
        season = self.get_current_season()
        raw_matches = await self.api_client.get_fixtures_by_team_and_season(team_id, season)
        matches = self._normalize_fixtures(raw_matches)
        now = datetime.now(UTC)

        if direction == "next":
            filtered = [
                match
                for match in matches
                if match.get("date") and self._parse_match_datetime(match["date"]) >= now
            ]
            filtered.sort(key=lambda match: match.get("date") or "")
        else:
            filtered = [
                match
                for match in matches
                if match.get("date") and self._parse_match_datetime(match["date"]) <= now
            ]
            filtered.sort(key=lambda match: match.get("date") or "", reverse=True)

        return filtered[:limit]

    async def _fallback_upcoming_matches(self, limit: int):
        today = datetime.now(UTC).date()
        dates_to_try = [
            today,
            today + timedelta(days=1),
        ]
        collected = []
        now = datetime.now(UTC)

        for date_value in dates_to_try:
            raw_matches = await self.api_client.get_fixtures_by_date(date_value.strftime("%Y-%m-%d"))
            collected.extend(self._normalize_fixtures(raw_matches))

        upcoming = [
            match
            for match in collected
            if match.get("date") and self._parse_match_datetime(match["date"]) >= now
        ]
        upcoming.sort(key=lambda match: match.get("date") or "")
        return upcoming[:limit]

    def _normalize_fixtures(self, fixtures: list[dict]):
        return [self._normalize_fixture(fixture) for fixture in fixtures if fixture]

    def _normalize_fixture(self, fixture: dict):
        if not fixture:
            return None

        fixture_data = fixture.get("fixture", {})
        teams = fixture.get("teams", {})
        league = fixture.get("league", {})
        goals = fixture.get("goals", {})

        return {
            "id": fixture_data.get("id"),
            "date": fixture_data.get("date"),
            "home": teams.get("home", {}).get("name", "Home"),
            "away": teams.get("away", {}).get("name", "Away"),
            "league_id": league.get("id"),
            "league": league.get("name", "Unknown league"),
            "country": league.get("country", "Unknown country"),
            "status": fixture_data.get("status", {}).get("short", ""),
            "status_long": fixture_data.get("status", {}).get("long", ""),
            "score": self._format_score(goals),
            "home_goals": goals.get("home"),
            "away_goals": goals.get("away"),
            "popularity_score": self._popularity_score(
                teams.get("home", {}).get("name", "Home"),
                teams.get("away", {}).get("name", "Away"),
                league.get("id"),
            ),
        }

    @staticmethod
    def _parse_match_datetime(value: str):
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)

    @staticmethod
    def _normalize_standings(rows: list[dict]):
        return [
            {
                "rank": row.get("rank"),
                "team": row.get("team", {}).get("name", "Unknown team"),
                "points": row.get("points", 0),
                "played": row.get("all", {}).get("played", 0),
            }
            for row in rows
        ]

    @staticmethod
    def _normalize_scorers(rows: list[dict]):
        scorers = []
        for row in rows:
            statistics = row.get("statistics", [{}])[0]
            scorers.append(
                {
                    "player": row.get("player", {}).get("name", "Unknown player"),
                    "team": statistics.get("team", {}).get("name", "Unknown team"),
                    "goals": statistics.get("goals", {}).get("total") or 0,
                }
            )
        return scorers

    @staticmethod
    def _normalize_events(rows: list[dict]):
        events = []
        for row in rows:
            time_info = row.get("time", {})
            minute = time_info.get("elapsed")
            extra = time_info.get("extra")
            events.append(
                {
                    "team": row.get("team", {}).get("name", "Unknown team"),
                    "player": row.get("player", {}).get("name") or "Unknown player",
                    "assist": row.get("assist", {}).get("name"),
                    "type": row.get("type", "Event"),
                    "detail": row.get("detail", ""),
                    "comments": row.get("comments"),
                    "minute": minute,
                    "extra": extra,
                }
            )
        return events

    @staticmethod
    def _normalize_statistics(rows: list[dict]):
        statistics = []
        for row in rows:
            team_name = row.get("team", {}).get("name", "Unknown team")
            entries = []
            for item in row.get("statistics", []):
                value = item.get("value")
                if value in (None, ""):
                    continue
                entries.append({"type": item.get("type", "Stat"), "value": value})
            statistics.append({"team": team_name, "entries": entries})
        return statistics

    @staticmethod
    def _normalize_lineups(rows: list[dict]):
        lineups = []
        for row in rows:
            lineups.append(
                {
                    "team": row.get("team", {}).get("name", "Unknown team"),
                    "formation": row.get("formation") or "Unknown",
                    "coach": row.get("coach", {}).get("name") or "Unknown coach",
                    "start_xi": [
                        {
                            "name": player.get("player", {}).get("name", "Unknown player"),
                            "number": player.get("player", {}).get("number"),
                            "pos": player.get("player", {}).get("pos"),
                        }
                        for player in row.get("startXI", [])
                    ],
                    "substitutes": [
                        {
                            "name": player.get("player", {}).get("name", "Unknown player"),
                            "number": player.get("player", {}).get("number"),
                            "pos": player.get("player", {}).get("pos"),
                        }
                        for player in row.get("substitutes", [])
                    ],
                }
            )
        return lineups

    @staticmethod
    def _normalize_players(rows: list[dict]):
        players = []
        for row in rows:
            team_name = row.get("team", {}).get("name", "Unknown team")
            for player in row.get("players", []):
                stats = (player.get("statistics") or [{}])[0]
                rating = stats.get("games", {}).get("rating")
                try:
                    rating_value = float(rating) if rating not in (None, "") else None
                except (TypeError, ValueError):
                    rating_value = None
                players.append(
                    {
                        "team": team_name,
                        "name": player.get("player", {}).get("name", "Unknown player"),
                        "position": stats.get("games", {}).get("position") or "N/A",
                        "minutes": stats.get("games", {}).get("minutes"),
                        "rating": rating,
                        "rating_value": rating_value,
                        "goals": stats.get("goals", {}).get("total") or 0,
                        "assists": stats.get("goals", {}).get("assists") or 0,
                        "shots": stats.get("shots", {}).get("total") or 0,
                        "passes": stats.get("passes", {}).get("total") or 0,
                        "tackles": stats.get("tackles", {}).get("total") or 0,
                        "duels": stats.get("duels", {}).get("total") or 0,
                        "yellow": stats.get("cards", {}).get("yellow") or 0,
                        "red": stats.get("cards", {}).get("red") or 0,
                    }
                )

        return sorted(
            players,
            key=lambda player: (
                player.get("rating_value") is not None,
                player.get("rating_value") or 0,
                player.get("minutes") or 0,
            ),
            reverse=True,
        )

    @staticmethod
    def _format_score(goals: dict):
        home = goals.get("home")
        away = goals.get("away")
        if home is None or away is None:
            return "-"
        return f"{home}:{away}"

    @staticmethod
    def _popularity_score(home: str, away: str, league_id: int | None):
        return (
            LEAGUE_POPULARITY.get(league_id, 0)
            + TEAM_POPULARITY.get(home, 0)
            + TEAM_POPULARITY.get(away, 0)
        )

    @staticmethod
    def _sort_by_popularity(matches: list[dict]):
        return sorted(
            matches,
            key=lambda match: (
                match.get("popularity_score", 0),
                match.get("status") in {"1H", "2H", "HT", "ET", "P"},
                match.get("date") or "",
            ),
            reverse=True,
        )

    def _supported_seasons_for_plan(self):
        current = self.get_current_season()
        latest_allowed = min(current, 2024)
        seasons = list(range(latest_allowed, 2021, -1))
        return seasons or [latest_allowed]
