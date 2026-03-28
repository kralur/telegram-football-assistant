class AnalysisService:

    def __init__(self, openai_client):
        self.openai_client = openai_client

    async def analyze(self, match: dict):

        prompt = (
            f"Provide a short football match analysis.\n\n"
            f"Match: {match['home']} vs {match['away']}\n"
            f"League: {match['league']}\n"
            f"Date: {match['date']}\n\n"
            f"Include:\n"
            f"- Key strengths\n"
            f"- Form insights\n"
            f"- Expected result\n"
            f"- Predicted score"
        )

        result = await self.openai_client.analyze_match(prompt)

        if not result:
            return (
                "⚠ AI analysis temporarily unavailable.\n\n"
                "Expect a competitive match with tactical battles and key moments deciding the outcome."
            )

        return result