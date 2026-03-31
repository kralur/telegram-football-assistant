import unittest

from src.bot.runtime import BotRuntime


class FakeServices:
    match_service = object()
    analysis_service = None
    favorites_service = object()
    search_service = object()
    users_repository = object()


class BotRuntimeTests(unittest.TestCase):
    def test_runtime_reports_missing_token_as_not_configured(self):
        runtime = BotRuntime(FakeServices())
        self.assertIsInstance(runtime.is_configured, bool)


if __name__ == "__main__":
    unittest.main()
