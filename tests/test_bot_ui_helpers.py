import unittest

from src.bot.keyboards import match_card_keyboard, today_filter_keyboard
from src.bot.pagination import paginate
from src.bot.views import favorites_text, format_datetime, match_card_text, matches_text


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

    def test_favorites_text_shows_next_and_last_match(self):
        text = favorites_text(
            [
                {
                    "team_name": "Arsenal",
                    "next_match": {
                        "home": "Arsenal",
                        "away": "Chelsea",
                        "date": "2026-03-31T18:00:00+00:00",
                    },
                    "last_match": {
                        "home": "Liverpool",
                        "away": "Arsenal",
                        "score": "2:1",
                    },
                }
            ],
            pending_count=2,
            timezone="Asia/Tashkent",
            page=0,
            total_pages=1,
        )

        self.assertIn("Next: Arsenal vs Chelsea", text)
        self.assertIn("Last: Liverpool vs Arsenal 2:1", text)

    def test_matches_text_formats_match_blocks(self):
        text = matches_text(
            "Today's matches",
            [
                {
                    "home": "Arsenal",
                    "away": "Chelsea",
                    "score": "-",
                    "country": "England",
                    "league": "Premier League",
                    "date": "2026-03-31T18:00:00+00:00",
                    "status_long": "Not Started",
                }
            ],
            timezone="Asia/Tashkent",
            page=0,
            total_pages=1,
        )

        self.assertIn("[1] Arsenal vs Chelsea", text)
        self.assertIn("League: England - Premier League", text)
        self.assertIn("Time: 2026-03-31 23:00 | Not Started", text)

    def test_match_card_text_formats_single_match(self):
        text = match_card_text(
            "Today's matches",
            {
                "home": "Arsenal",
                "away": "Chelsea",
                "score": "-",
                "country": "England",
                "league": "Premier League",
                "date": "2026-03-31T18:00:00+00:00",
                "status_long": "Not Started",
            },
            timezone="Asia/Tashkent",
            page=0,
            total_pages=44,
        )

        self.assertIn("Today's matches (1/44)", text)
        self.assertIn("Arsenal vs Chelsea", text)
        self.assertIn("League: England - Premier League", text)

    def test_match_card_keyboard_has_single_match_actions(self):
        markup = match_card_keyboard(
            {"id": 1, "home": "Arsenal", "away": "Chelsea"},
            page=0,
            total_pages=44,
        )

        rows = markup.inline_keyboard
        self.assertEqual([button.text for button in rows[0]], ["Details", "Notify", "AI"])
        self.assertEqual([button.text for button in rows[1]], ["Filter league"])
        self.assertEqual([button.text for button in rows[2]], ["1/44", "Next"])

    def test_today_filter_keyboard_marks_selected_league(self):
        markup = today_filter_keyboard(
            [{"id": 39, "name": "Premier League"}, {"id": 140, "name": "La Liga"}],
            selected_league_id=39,
        )

        rows = markup.inline_keyboard
        self.assertEqual(rows[0][0].text, "All leagues")
        self.assertEqual(rows[1][0].text, "Premier League *")


if __name__ == "__main__":
    unittest.main()
