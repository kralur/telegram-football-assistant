import os
import unittest

from src.run import resolve_runtime


class RunModuleTests(unittest.TestCase):
    def test_resolve_runtime_prefers_explicit_app_runtime(self):
        original = os.environ.get("APP_RUNTIME")
        try:
            os.environ["APP_RUNTIME"] = "bot"
            self.assertEqual(resolve_runtime(), "bot")
        finally:
            if original is None:
                os.environ.pop("APP_RUNTIME", None)
            else:
                os.environ["APP_RUNTIME"] = original


if __name__ == "__main__":
    unittest.main()
