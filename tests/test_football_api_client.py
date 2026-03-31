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
    async def test_get_raises_clear_error_when_api_key_missing(self):
        client = FootballApiClient.__new__(FootballApiClient)
        client.client = None
        client.logger = FakeLogger()

        with self.assertRaises(FootballApiError) as context:
            await client._get("/fixtures", {"date": "2026-03-28"})

        self.assertEqual(str(context.exception), "API key is not configured")

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
            "Daily API request limit reached. Football data is temporarily unavailable. Please try again later.",
        )
        self.assertTrue(client.logger.warnings)

    def test_build_user_error_message_for_season_limit(self):
        message = FootballApiClient._build_user_error_message(
            "plan: Free plans do not have access to this season, try from 2022 to 2024."
        )

        self.assertEqual(
            message,
            "The latest season is not available on the current API plan. The bot will try an older supported season where possible.",
        )

    def test_build_user_error_message_for_plan_restriction(self):
        message = FootballApiClient._build_user_error_message(
            "plan: Free plans do not have access to this endpoint."
        )

        self.assertEqual(
            message,
            "This football data is not available on the current API plan.",
        )


if __name__ == "__main__":
    unittest.main()
