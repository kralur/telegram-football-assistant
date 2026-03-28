import unittest

from src.bot.pagination import paginate
from src.bot.views import format_datetime


class BotUiHelperTests(unittest.TestCase):
    def test_paginate_returns_requested_page(self):
        items = [{"id": index} for index in range(12)]
        page_items, page, total_pages = paginate(items, page=1, page_size=5)

        self.assertEqual(page, 1)
        self.assertEqual(total_pages, 3)
        self.assertEqual([item["id"] for item in page_items], [5, 6, 7, 8, 9])

    def test_format_datetime_uses_requested_timezone(self):
        formatted = format_datetime("2026-03-28T15:00:00+00:00", "Asia/Tashkent")
        self.assertEqual(formatted, "2026-03-28 20:00")


if __name__ == "__main__":
    unittest.main()
