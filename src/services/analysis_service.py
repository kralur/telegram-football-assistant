class AnalysisService:
    def __init__(self, openai_client, cache):
        self.openai_client = openai_client
        self.cache = cache

    async def analyze(self, match: dict):
        match_id = match.get("id", "unknown")
        cache_key = f"analysis:{match_id}"

        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        prompt = (
            "Provide a short football match analysis.\n\n"
            f"Match: {match['home']} vs {match['away']}\n"
            f"League: {match['league']}\n"
            f"Kickoff: {match['date']}\n"
            f"Current status: {match.get('status_long', 'Unknown')}\n"
            f"Current score: {match.get('score', '-')}\n\n"
            "Include:\n"
            "- Key tactical angle\n"
            "- What to watch for\n"
            "- Short prediction or expectation\n"
            "- Keep it concise and readable for Telegram"
        )

        result = await self.openai_client.analyze_match(prompt) if self.openai_client else None

        if not result:
            result = (
                "AI analysis is temporarily unavailable.\n\n"
                "This looks like a competitive match. Watch the tactical battle, momentum swings, "
                "and transitions between attack and defense."
            )

        self.cache.set(cache_key, result, ttl=900)
        return result
