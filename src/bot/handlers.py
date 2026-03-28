from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    CallbackQuery
)


def setup_handlers(
    match_service,
    favorites_service,
    analysis_service,
    users_repository
):
    router = Router()
    user_state = {}

    # =============================
    # MAIN MENU
    # =============================

    reply_menu = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚽ Matches")],
            [KeyboardButton(text="🔎 Search Team")],
            [KeyboardButton(text="⭐ Favorites")],
            [KeyboardButton(text="⚙️ Settings")]
        ],
        resize_keyboard=True
    )

    def back_button():
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Back", callback_data="back_main")]
            ]
        )

    # =============================
    # START
    # =============================

    @router.message(CommandStart())
    async def start_handler(message: Message):
        users_repository.add(message.from_user.id)
        user_state.pop(message.from_user.id, None)

        await message.answer("⚽ Football Assistant", reply_markup=reply_menu)

    # =============================
    # BACK
    # =============================

    @router.callback_query(lambda c: c.data == "back_main")
    async def back_main(callback: CallbackQuery):
        user_state.pop(callback.from_user.id, None)

        await callback.message.delete()
        await callback.message.answer("⚽ Main Menu", reply_markup=reply_menu)

    # =============================
    # MATCHES
    # =============================

    @router.message(lambda m: m.text == "⚽ Matches")
    async def show_matches(message: Message):
        user_state.pop(message.from_user.id, None)

        fixtures = await match_service.get_today_matches()

        if not fixtures:
            await message.answer("No matches today.")
            return

        matches = fixtures[:5]
        user_state[message.from_user.id] = {"matches": matches}

        text = "⚽ Today's Matches\n\n"
        keyboard = []

        for i, match in enumerate(matches, 1):
            home = match["teams"]["home"]["name"]
            away = match["teams"]["away"]["name"]

            text += f"{i}. {home} vs {away}\n"

            keyboard.append([
                InlineKeyboardButton(
                    text=f"Open Match {i}",
                    callback_data=f"open_match:{i}"
                )
            ])

        keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_main")])

        await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

    @router.callback_query(lambda c: c.data.startswith("open_match:"))
    async def open_match(callback: CallbackQuery):
        index = int(callback.data.split(":")[1]) - 1
        matches = user_state.get(callback.from_user.id, {}).get("matches", [])

        if index >= len(matches):
            await callback.answer("Invalid match")
            return

        match = matches[index]

        home = match["teams"]["home"]["name"]
        away = match["teams"]["away"]["name"]
        league = match["league"]["name"]
        date = match["fixture"]["date"][:16].replace("T", " ")

        match_id = match_service.cache_match({
            "home": home,
            "away": away,
            "league": league,
            "date": date
        })

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🤖 Analyze", callback_data=f"analyze:{match_id}")],
                [InlineKeyboardButton(text=f"⭐ Add {home}", callback_data=f"addfav:{home}")],
                [InlineKeyboardButton(text=f"⭐ Add {away}", callback_data=f"addfav:{away}")],
                [InlineKeyboardButton(text="🔙 Back", callback_data="back_main")]
            ]
        )

        await callback.message.edit_text(
            f"🏟 {league}\n\n⚔ {home} vs {away}\n\n🕒 {date}",
            reply_markup=keyboard
        )

    # =============================
    # ADD FAVORITE
    # =============================

    @router.callback_query(lambda c: c.data.startswith("addfav:"))
    async def add_favorite(callback: CallbackQuery):
        team_name = callback.data.split("addfav:")[1]

        favorites_service.add_team(callback.from_user.id, team_name)

        await callback.answer("Added to favorites ⭐")

    # =============================
    # SEARCH
    # =============================

    @router.message(lambda m: m.text == "🔎 Search Team")
    async def start_search(message: Message):
        user_state[message.from_user.id] = {"mode": "search"}
        await message.answer("Type team name")

    @router.message(lambda m: user_state.get(m.from_user.id, {}).get("mode") == "search")
    async def handle_search(message: Message):
        query = message.text.strip()

        teams = await match_service.search_team(query)

        if not teams:
            await message.answer(
                "No teams found.",
                reply_markup=back_button()
            )
            return

        keyboard = []

        for team in teams[:5]:
            team_id = team["team"]["id"]
            team_name = team["team"]["name"]

            keyboard.append([
                InlineKeyboardButton(
                    text=team_name,
                    callback_data=f"search_team:{team_id}"
                )
            ])

        keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_main")])

        await message.answer(
            "Select team:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

    # =============================
    # FAVORITES
    # =============================

    @router.message(lambda m: m.text == "⭐ Favorites")
    async def show_favorites(message: Message):
        user_state.pop(message.from_user.id, None)

        favorites = favorites_service.get_user_favorites(message.from_user.id)

        if not favorites:
            await message.answer("No favorite teams.")
            return

        text = "⭐ Favorite Teams\n\n"
        for team in favorites:
            text += f"• {team}\n"

        await message.answer(text)

    # =============================
    # SETTINGS
    # =============================

    @router.message(lambda m: m.text == "⚙️ Settings")
    async def show_settings(message: Message):
        user_state.pop(message.from_user.id, None)

        timezone, daily_enabled, reminders_enabled = users_repository.get_settings(message.from_user.id)

        await message.answer(
            f"⚙ Settings\n\n"
            f"Timezone: {timezone}\n"
            f"Daily Summary: {'ON' if daily_enabled else 'OFF'}\n"
            f"Reminders: {'ON' if reminders_enabled else 'OFF'}"
        )

    return router