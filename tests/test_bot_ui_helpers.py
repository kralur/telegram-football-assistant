import unittest

from src.bot.keyboards import (
    main_menu_keyboard,
    match_card_keyboard,
    match_detail_keyboard,
    today_filter_keyboard,
)
from src.bot.pagination import paginate
from src.bot.views import (
    favorites_text,
    format_datetime,
    match_card_text,
    match_events_text,
    match_lineups_text,
    match_players_text,
    match_statistics_text,
    matches_text,
)


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

    def test_main_menu_keyboard_includes_webapp_button(self):
        markup = main_menu_keyboard()

        first_row = markup.inline_keyboard[0]
        self.assertEqual(first_row[0].text, "⚽ Open Match Center")
        self.assertIsNotNone(first_row[0].web_app)
        labels = [button.text for row in markup.inline_keyboard[1:] for button in row]
        self.assertNotIn("Standings", labels)
        self.assertNotIn("Scorers", labels)

    def test_today_filter_keyboard_marks_selected_league(self):
        markup = today_filter_keyboard(
            [{"id": 39, "name": "Premier League"}, {"id": 140, "name": "La Liga"}],
            selected_league_id=39,
        )

        rows = markup.inline_keyboard
        self.assertEqual(rows[0][0].text, "All leagues")
        self.assertEqual(rows[1][0].text, "Premier League *")

    def test_match_detail_keyboard_marks_active_section(self):
        markup = match_detail_keyboard(match_id=55, active="events")

        rows = markup.inline_keyboard
        self.assertEqual([button.text for button in rows[0]], ["Summary", "Events *", "Stats"])
        self.assertEqual([button.text for button in rows[1]], ["Lineups", "Players"])

    def test_match_events_text_formats_timeline(self):
        text = match_events_text(
            {"home": "Real Madrid", "away": "Barcelona", "date": "2026-03-31T18:00:00+00:00"},
            [
                {
                    "minute": 15,
                    "extra": None,
                    "team": "Real Madrid",
                    "player": "Vinicius Junior",
                    "type": "Goal",
                    "detail": "Normal Goal",
                    "assist": "Bellingham",
                    "comments": None,
                }
            ],
            "Asia/Tashkent",
        )

        self.assertIn("15' Real Madrid", text)
        self.assertIn("Goal: Vinicius Junior - Normal Goal", text)

    def test_match_statistics_text_formats_team_blocks(self):
        text = match_statistics_text(
            {"home": "Real Madrid", "away": "Barcelona", "date": "2026-03-31T18:00:00+00:00"},
            [{"team": "Real Madrid", "entries": [{"type": "Shots on Goal", "value": 6}]}],
            "Asia/Tashkent",
        )

        self.assertIn("Real Madrid", text)
        self.assertIn("- Shots on Goal: 6", text)

    def test_match_lineups_text_formats_sections(self):
        text = match_lineups_text(
            {"home": "Real Madrid", "away": "Barcelona", "date": "2026-03-31T18:00:00+00:00"},
            [
                {
                    "team": "Real Madrid",
                    "formation": "4-3-3",
                    "coach": "Carlo Ancelotti",
                    "start_xi": [{"name": "Courtois", "number": 1, "pos": "G"}],
                    "substitutes": [{"name": "Modric", "number": 10, "pos": "M"}],
                }
            ],
            "Asia/Tashkent",
        )

        self.assertIn("Formation: 4-3-3", text)
        self.assertIn("Starting XI:", text)
        self.assertIn("- #1 Courtois (G)", text)

    def test_match_players_text_formats_top_players(self):
        text = match_players_text(
            {"home": "Real Madrid", "away": "Barcelona", "date": "2026-03-31T18:00:00+00:00"},
            [
                {
                    "team": "Real Madrid",
                    "name": "Bellingham",
                    "position": "M",
                    "minutes": 90,
                    "rating": "8.2",
                    "goals": 1,
                    "assists": 0,
                    "shots": 3,
                    "passes": 48,
                    "tackles": 2,
                    "duels": 9,
                    "yellow": 1,
                    "red": 0,
                }
            ],
            "Asia/Tashkent",
        )

        self.assertIn("Bellingham | Real Madrid", text)
        self.assertIn("Rating: 8.2", text)


if __name__ == "__main__":
    unittest.main()
