from src.config.settings import CACHE_TTL_SEARCH

POPULAR_TEAM_CATALOG = [
    {"id": 541, "name": "Real Madrid", "country": "Spain", "popularity": 100},
    {"id": 529, "name": "Barcelona", "country": "Spain", "popularity": 100},
    {"id": 530, "name": "Atletico Madrid", "country": "Spain", "popularity": 85},
    {"id": 533, "name": "Villarreal", "country": "Spain", "popularity": 70},
    {"id": 548, "name": "Real Sociedad", "country": "Spain", "popularity": 75},
    {"id": 543, "name": "Real Betis", "country": "Spain", "popularity": 75},
    {"id": 50, "name": "Manchester City", "country": "England", "popularity": 95},
    {"id": 33, "name": "Manchester United", "country": "England", "popularity": 95},
    {"id": 40, "name": "Liverpool", "country": "England", "popularity": 95},
    {"id": 42, "name": "Arsenal", "country": "England", "popularity": 92},
    {"id": 49, "name": "Chelsea", "country": "England", "popularity": 88},
    {"id": 47, "name": "Tottenham", "country": "England", "popularity": 82},
    {"id": 157, "name": "Bayern Munich", "country": "Germany", "popularity": 93},
    {"id": 165, "name": "Borussia Dortmund", "country": "Germany", "popularity": 82},
    {"id": 85, "name": "PSG", "country": "France", "popularity": 92},
    {"id": 496, "name": "Juventus", "country": "Italy", "popularity": 88},
    {"id": 489, "name": "AC Milan", "country": "Italy", "popularity": 84},
    {"id": 505, "name": "Inter", "country": "Italy", "popularity": 84},
]


class SearchService:
    def __init__(self, match_service, cache):
        self.match_service = match_service
        self.cache = cache

    async def search_teams(self, query: str):
        normalized_query = " ".join(query.lower().split())
        if not normalized_query:
            return []

        cache_key = f"search:{normalized_query}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        raw_results = await self.match_service.search_team(query)
        api_results = [
            {
                "id": item.get("team", {}).get("id"),
                "name": item.get("team", {}).get("name", "Unknown team"),
                "country": item.get("country") or "Unknown country",
                "popularity": 0,
            }
            for item in raw_results
            if item.get("team", {}).get("id") is not None
        ]

        fallback_results = self._fallback_search(normalized_query)
        results = self._merge_and_rank(normalized_query, api_results, fallback_results)

        self.cache.set(cache_key, results, ttl=CACHE_TTL_SEARCH)
        return results

    def _fallback_search(self, normalized_query: str):
        query_parts = normalized_query.split()
        matches = []
        for team in POPULAR_TEAM_CATALOG:
            team_name = team["name"].lower()
            if all(part in team_name for part in query_parts):
                matches.append(dict(team))
        return matches

    @staticmethod
    def _merge_and_rank(normalized_query: str, api_results: list[dict], fallback_results: list[dict]):
        merged = {}
        for item in api_results + fallback_results:
            key = item["name"].lower()
            merged[key] = {
                "id": item["id"],
                "name": item["name"],
                "country": item["country"],
                "popularity": max(item.get("popularity", 0), merged.get(key, {}).get("popularity", 0)),
            }

        def score(team: dict):
            team_name = team["name"].lower()
            starts = 1 if team_name.startswith(normalized_query) else 0
            contains = 1 if normalized_query in team_name else 0
            return (starts, contains, team.get("popularity", 0), team["name"])

        return sorted(merged.values(), key=score, reverse=True)
