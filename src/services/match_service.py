import uuid


class MatchService:

    def __init__(self, api_client, cache):
        self.api_client = api_client
        self.cache = cache
        self._match_cache = {}

    async def get_today_matches(self):
        cache_key = "today_matches"

        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        fixtures = await self.api_client.get_today_fixtures()

        self.cache.set(cache_key, fixtures, ttl=300)
        return fixtures

    async def search_team(self, query: str):
        return await self.api_client.search_team(query)

    async def get_team_matches(self, team_id: int):
        return await self.api_client.get_next_fixtures_by_team_id(team_id)

    def cache_match(self, match_data: dict):
        match_id = str(uuid.uuid4())[:8]
        self._match_cache[match_id] = match_data
        return match_id

    def get_cached_match(self, match_id: str):
        return self._match_cache.get(match_id)