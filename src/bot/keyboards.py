from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.config.settings import WEBAPP_URL

TIMEZONE_OPTIONS = [
    ("UTC", "UTC"),
    ("Europe/London", "London"),
    ("Europe/Berlin", "Berlin"),
    ("Europe/Madrid", "Madrid"),
    ("Europe/Rome", "Rome"),
    ("Europe/Paris", "Paris"),
    ("Asia/Tashkent", "Tashkent"),
]


def main_menu_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Today", callback_data="nav:today")
    kb.button(text="Live", callback_data="nav:live")
    kb.button(text="Favorites", callback_data="nav:favorites")
    kb.button(text="Search", callback_data="nav:search")
    kb.button(text="Timezone", callback_data="nav:timezone")
    kb.button(text="Help", callback_data="nav:help")
    kb.adjust(2)

    rows = kb.export()
    if WEBAPP_URL.startswith("https://"):
        rows.insert(
            0,
            [
                InlineKeyboardButton(
                    text="Open Match Center",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            ],
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def footer_navigation(kb: InlineKeyboardBuilder, include_back: bool = True):
    if include_back:
        kb.button(text="Back", callback_data="nav:back")
    kb.button(text="Main menu", callback_data="nav:main")


def back_keyboard(target: str = "nav:back"):
    kb = InlineKeyboardBuilder()
    kb.button(text="Back", callback_data=target)
    kb.button(text="Main menu", callback_data="nav:main")
    kb.adjust(2)
    return kb.as_markup()


def league_picker_keyboard(leagues: list[dict], prefix: str):
    kb = InlineKeyboardBuilder()
    for league in leagues:
        kb.button(text=league["name"], callback_data=f"{prefix}:{league['id']}")
    footer_navigation(kb)
    kb.adjust(1)
    return kb.as_markup()


def today_filter_keyboard(leagues: list[dict], selected_league_id: int | None = None):
    kb = InlineKeyboardBuilder()
    all_title = "All leagues *" if selected_league_id is None else "All leagues"
    kb.button(text=all_title, callback_data="today_filter:all")
    for league in leagues:
        title = f"{league['name']} {'*' if league['id'] == selected_league_id else ''}".strip()
        kb.button(text=title, callback_data=f"today_filter:{league['id']}")
    footer_navigation(kb)
    kb.adjust(1)
    return kb.as_markup()


def pagination_row(kb: InlineKeyboardBuilder, page: int, total_pages: int):
    if total_pages <= 1:
        return
    if page > 0:
        kb.button(text="Prev", callback_data=f"page:{page - 1}")
    kb.button(text=f"{page + 1}/{total_pages}", callback_data="noop")
    if page < total_pages - 1:
        kb.button(text="Next", callback_data=f"page:{page + 1}")


def match_list_keyboard(matches: list[dict], page: int, total_pages: int):
    kb = InlineKeyboardBuilder()
    for index, match in enumerate(matches, start=1):
        if match.get("id") is not None:
            kb.button(
                text=f"[{index}] {match['home']} vs {match['away']}",
                callback_data="noop",
            )
            kb.button(text="Details", callback_data=f"match:open:{match['id']}")
            kb.button(text="Notify", callback_data=f"notify:match:{match['id']}")
            kb.button(text="AI", callback_data=f"analysis:match:{match['id']}")
    pagination_row(kb, page, total_pages)
    footer_navigation(kb)
    layout = []
    for _ in matches:
        layout.extend([1, 3])
    if total_pages > 1:
        if page > 0 and page < total_pages - 1:
            layout.append(3)
        else:
            layout.append(2)
    layout.append(2)
    kb.adjust(*layout)
    return kb.as_markup()


def match_card_keyboard(match: dict | None, page: int, total_pages: int):
    kb = InlineKeyboardBuilder()
    if match and match.get("id") is not None:
        kb.button(text="Details", callback_data=f"match:open:{match['id']}")
        kb.button(text="Notify", callback_data=f"notify:match:{match['id']}")
        kb.button(text="AI", callback_data=f"analysis:match:{match['id']}")
    kb.button(text="Filter league", callback_data="nav:today_filter")
    pagination_row(kb, page, total_pages)
    footer_navigation(kb)
    layout = []
    if match and match.get("id") is not None:
        layout.append(3)
    layout.append(1)
    if total_pages > 1:
        if page > 0 and page < total_pages - 1:
            layout.append(3)
        else:
            layout.append(2)
    layout.append(2)
    kb.adjust(*layout)
    return kb.as_markup()


def search_results_keyboard(results: list[dict], page: int, total_pages: int, offset: int = 0):
    kb = InlineKeyboardBuilder()
    for index, team in enumerate(results):
        kb.button(
            text=f"Add {team['name']}",
            callback_data=f"favorite:add:{offset + index}",
        )
    pagination_row(kb, page, total_pages)
    footer_navigation(kb)
    kb.adjust(1)
    return kb.as_markup()


def favorites_keyboard(favorites: list[dict], page: int, total_pages: int, offset: int = 0):
    kb = InlineKeyboardBuilder()
    for index, team in enumerate(favorites):
        next_match = team.get("next_match") or {}
        if next_match.get("id") is not None:
            kb.button(
                text="Open next",
                callback_data=f"favorite:open_next:{offset + index}",
            )
            kb.button(
                text="Notify next",
                callback_data=f"favorite:notify_next:{offset + index}",
            )
        kb.button(
            text=f"Remove {team['team_name']}",
            callback_data=f"favorite:remove:{offset + index}",
        )
    pagination_row(kb, page, total_pages)
    footer_navigation(kb)
    kb.adjust(2, 1, 2, 1, 2, 1, 2)
    return kb.as_markup()


def timezone_keyboard(current_timezone: str):
    kb = InlineKeyboardBuilder()
    for index, (value, label) in enumerate(TIMEZONE_OPTIONS):
        title = f"{label} {'*' if value == current_timezone else ''}".strip()
        kb.button(text=title, callback_data=f"timezone:set:{index}")
    footer_navigation(kb)
    kb.adjust(1)
    return kb.as_markup()


def match_detail_keyboard(match_id: int, active: str = "summary"):
    kb = InlineKeyboardBuilder()
    summary_title = "Summary *" if active == "summary" else "Summary"
    events_title = "Events *" if active == "events" else "Events"
    stats_title = "Stats *" if active == "statistics" else "Stats"
    lineups_title = "Lineups *" if active == "lineups" else "Lineups"
    players_title = "Players *" if active == "players" else "Players"
    ai_title = "AI *" if active == "analysis" else "AI"

    kb.button(text=summary_title, callback_data=f"match:open:{match_id}")
    kb.button(text=events_title, callback_data=f"match:events:{match_id}")
    kb.button(text=stats_title, callback_data=f"match:statistics:{match_id}")
    kb.button(text=lineups_title, callback_data=f"match:lineups:{match_id}")
    kb.button(text=players_title, callback_data=f"match:players:{match_id}")
    kb.button(text="Notify", callback_data=f"notify:match:{match_id}")
    kb.button(text=ai_title, callback_data=f"analysis:match:{match_id}")
    footer_navigation(kb)
    kb.adjust(3, 2, 2, 2)
    return kb.as_markup()


def table_screen_keyboard(page: int, total_pages: int):
    kb = InlineKeyboardBuilder()
    pagination_row(kb, page, total_pages)
    footer_navigation(kb)
    kb.adjust(3, 2)
    return kb.as_markup()
