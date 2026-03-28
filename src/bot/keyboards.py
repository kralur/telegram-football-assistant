from aiogram.utils.keyboard import InlineKeyboardBuilder

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
    kb.button(text="Standings", callback_data="nav:standings_leagues")
    kb.button(text="Scorers", callback_data="nav:scorers_leagues")
    kb.button(text="Favorites", callback_data="nav:favorites")
    kb.button(text="Search", callback_data="nav:search")
    kb.button(text="Timezone", callback_data="nav:timezone")
    kb.button(text="Help", callback_data="nav:help")
    kb.adjust(2)
    return kb.as_markup()


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
    for match in matches:
        if match.get("id") is not None:
            kb.button(text="Details", callback_data=f"match:open:{match['id']}")
            kb.button(text="Notify", callback_data=f"notify:match:{match['id']}")
            kb.button(text="AI", callback_data=f"analysis:match:{match['id']}")
    pagination_row(kb, page, total_pages)
    footer_navigation(kb)
    kb.adjust(3, 3, 3, 3, 3, 2, 2)
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
        kb.button(
            text=f"Remove {team['team_name']}",
            callback_data=f"favorite:remove:{offset + index}",
        )
    pagination_row(kb, page, total_pages)
    footer_navigation(kb)
    kb.adjust(1)
    return kb.as_markup()


def timezone_keyboard(current_timezone: str):
    kb = InlineKeyboardBuilder()
    for index, (value, label) in enumerate(TIMEZONE_OPTIONS):
        title = f"{label} {'*' if value == current_timezone else ''}".strip()
        kb.button(text=title, callback_data=f"timezone:set:{index}")
    footer_navigation(kb)
    kb.adjust(1)
    return kb.as_markup()


def match_detail_keyboard(match_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="Notify", callback_data=f"notify:match:{match_id}")
    kb.button(text="AI analysis", callback_data=f"analysis:match:{match_id}")
    footer_navigation(kb)
    kb.adjust(2, 2)
    return kb.as_markup()


def table_screen_keyboard(page: int, total_pages: int):
    kb = InlineKeyboardBuilder()
    pagination_row(kb, page, total_pages)
    footer_navigation(kb)
    kb.adjust(3, 2)
    return kb.as_markup()
