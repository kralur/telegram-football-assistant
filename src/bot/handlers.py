from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from src.services.football_api import get_today_fixtures
from src.services.football_api import get_today_fixtures, get_fixtures_by_date
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from src.services.football_api import get_fixtures_by_date
from src.services.football_api import get_league_standings
from src.db.database import add_favorite, get_favorites


router = Router()

@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "👋 Привет! Я футбольный ассистент.\n"
        "Выбери действие ниже 👇",
        reply_markup=menu_keyboard
    )

@router.message(lambda msg: msg.text == "/today")
async def today_matches(message: Message):
    try:
        fixtures = get_today_fixtures()

        if not fixtures:
            await message.answer("Сегодня матчей не найдено ⚽")
            return

        text = "⚽ Матчи сегодня:\n\n"

        for match in fixtures[:5]:
            home = match["teams"]["home"]["name"]
            away = match["teams"]["away"]["name"]
            date = match["fixture"]["date"][:16].replace("T", " ")

            text += f"{home} vs {away}\n🕒 {date}\n\n"

        await message.answer(text)

    except Exception as e:
        await message.answer("Ошибка при получении матчей 😕")

@router.message(lambda msg: msg.text.startswith("/date"))
async def matches_by_date(message: Message):
    try:
        parts = message.text.split()

        if len(parts) != 2:
            await message.answer("Используй формат:\n/date YYYY-MM-DD")
            return

        date = parts[1]

        fixtures = get_fixtures_by_date(date)

        if not fixtures:
            await message.answer(f"На {date} матчей не найдено ⚽")
            return

        text = f"⚽ Матчи на {date}:\n\n"

        for match in fixtures[:5]:
            home = match["teams"]["home"]["name"]
            away = match["teams"]["away"]["name"]
            time = match["fixture"]["date"][11:16]

            text += f"{home} vs {away}\n🕒 {time}\n\n"

        await message.answer(text)

    except Exception:
        await message.answer("Ошибка при получении матчей 😕")

@router.message(lambda msg: msg.text.startswith("/fav"))
async def add_favorite_handler(message: Message):
    parts = message.text.split(maxsplit=1)

    if len(parts) != 2:
        await message.answer("Используй:\n/fav TEAM_NAME")
        return

    team_name = parts[1]
    user_id = message.from_user.id

    add_favorite(user_id, team_name)
    await message.answer(f"⭐ {team_name} добавлена в избранное!")


menu_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="⚽ Матчи сегодня", callback_data="today")
        ],
        [
            InlineKeyboardButton(text="📅 Матчи по дате", callback_data="date")
        ],
        [
            InlineKeyboardButton(text="🏆 Таблицы лиг", callback_data="standings")
        ],
        [
            InlineKeyboardButton(text="⭐ Избранные команды", callback_data="favorites")
        ],
        [
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")
        ],
    ]
)

date_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Сегодня", callback_data="date_today"),
            InlineKeyboardButton(text="⏭ Завтра", callback_data="date_tomorrow"),
        ],
        [
            InlineKeyboardButton(text="🗓 Ввести дату", callback_data="date_manual")
        ],
    ]
)

standings_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🇬🇧 Premier League", callback_data="pl"),
            InlineKeyboardButton(text="🇪🇸 La Liga", callback_data="laliga"),
        ],
        [
            InlineKeyboardButton(text="🇮🇹 Serie A", callback_data="seriea"),
            InlineKeyboardButton(text="🇩🇪 Bundesliga", callback_data="bundesliga"),
        ],
    ]
)



@router.callback_query(lambda c: c.data == "today")
async def today_callback(callback):
    from src.services.football_api import get_today_fixtures

    fixtures = get_today_fixtures()

    if not fixtures:
        await callback.message.answer("Сегодня матчей не найдено ⚽")
        return

    text = "⚽ Матчи сегодня:\n\n"

    for match in fixtures[:5]:
        home = match["teams"]["home"]["name"]
        away = match["teams"]["away"]["name"]
        time = match["fixture"]["date"][11:16]

        text += f"{home} vs {away}\n🕒 {time}\n\n"

    await callback.message.answer(text)

@router.callback_query(lambda c: c.data == "date")
async def date_menu(callback):
    await callback.message.answer(
        "📅 Выбери дату:",
        reply_markup=date_keyboard
    )

@router.callback_query(lambda c: c.data == "help")
async def help_callback(callback):
    await callback.message.answer(
        "ℹ️ Доступные функции:\n\n"
        "⚽ Матчи сегодня\n"
        "📅 Матчи по дате\n\n"
        "Пример:\n/date 2026-01-25"
    )

@router.callback_query(lambda c: c.data == "date_today")
async def date_today(callback):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    await send_matches_by_date(callback, today)

@router.callback_query(lambda c: c.data == "date_tomorrow")
async def date_tomorrow(callback):
    tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    await send_matches_by_date(callback, tomorrow)

@router.callback_query(lambda c: c.data == "date_manual")
async def date_manual(callback):
    await callback.message.answer(
        "🗓 Введи дату в формате:\n/date YYYY-MM-DD\n\nНапример:\n/date 2026-01-25"
    )

@router.callback_query(lambda c: c.data == "standings")
async def standings_menu(callback):
    await callback.message.answer(
        "🏆 Выбери лигу:",
        reply_markup=standings_keyboard
    )

@router.callback_query(lambda c: c.data == "pl")
async def pl_table(callback):
    await send_standings(callback, 39, "Premier League")


@router.callback_query(lambda c: c.data == "laliga")
async def laliga_table(callback):
    await send_standings(callback, 140, "La Liga")


@router.callback_query(lambda c: c.data == "seriea")
async def seriea_table(callback):
    await send_standings(callback, 135, "Serie A")


@router.callback_query(lambda c: c.data == "bundesliga")
async def bundesliga_table(callback):
    await send_standings(callback, 78, "Bundesliga")

@router.callback_query(lambda c: c.data == "favorites")
async def show_favorites(callback):
    user_id = callback.from_user.id
    favorites = get_favorites(user_id)

    if not favorites:
        await callback.message.answer("⭐ У тебя пока нет избранных команд.")
        return

    text = "⭐ Твои избранные команды:\n\n"
    for team in favorites:
        text += f"• {team}\n"

    await callback.message.answer(text)




async def send_matches_by_date(callback, date: str):
    fixtures = get_fixtures_by_date(date)

    if not fixtures:
        await callback.message.answer(f"На {date} матчей не найдено ⚽")
        return

    text = f"⚽ Матчи на {date}:\n\n"

    for match in fixtures[:5]:
        home = match["teams"]["home"]["name"]
        away = match["teams"]["away"]["name"]
        time = match["fixture"]["date"][11:16]

        text += f"{home} vs {away}\n🕒 {time}\n\n"

    await callback.message.answer(text)

async def send_standings(callback, league_id: int, title: str):
    standings = get_league_standings(league_id)

    if not standings:
        await callback.message.answer(
            f"🏆 {title}\n\nДанные таблицы пока недоступны ⚠️"
        )
        return

    text = f"🏆 {title} (Top 5)\n\n"

    for team in standings[:5]:
        pos = team["rank"]
        name = team["team"]["name"]
        pts = team["points"]

        text += f"{pos}. {name} — {pts} points ⭐\n"
        text += "\nЧтобы добавить в избранное:\n⭐ /fav TEAM_NAME"

    await callback.message.answer(text)

