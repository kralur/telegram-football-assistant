import unittest

from src.infrastructure.football_api_client import FootballApiClient, FootballApiError


class FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, payload: dict):
        self.payload = payload

    async def get(self, endpoint: str, params: dict):
        return FakeResponse(self.payload)


class FakeLogger:
    def __init__(self):
        self.warnings = []

    def warning(self, message, *args):
        self.warnings.append(message % args if args else message)

    def exception(self, message, *args):
        self.warnings.append(message % args if args else message)


class FootballApiClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_raises_user_friendly_error_on_payload_limit(self):
        client = FootballApiClient.__new__(FootballApiClient)
        client.client = FakeAsyncClient(
            {
                "get": "fixtures",
                "errors": {
                    "requests": "You have reached the request limit for the day.",
                },
                "response": [],
            }
        )
        client.logger = FakeLogger()

        with self.assertRaises(FootballApiError) as context:
            await client._get("/fixtures", {"date": "2026-03-28"})

        self.assertEqual(
            str(context.exception),
            "API request limit reached for today. Please try again later.",
        )
        self.assertTrue(client.logger.warnings)


if __name__ == "__main__":
    unittest.main()
