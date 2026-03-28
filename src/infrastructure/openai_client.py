import httpx
from src.config.settings import OPENAI_API_KEY


class OpenAIClient:

    BASE_URL = "https://api.openai.com/v1"

    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is missing")

        self.headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.headers,
            timeout=20.0
        )

    async def analyze_match(self, prompt: str):
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are a professional football analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 200
                }
            )

            response.raise_for_status()
            data = response.json()

            return data["choices"][0]["message"]["content"]

        except Exception:
            return None