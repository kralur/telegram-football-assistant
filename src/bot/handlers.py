from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import uuid

from src.services.football_api import (
    get_today_fixtures,
    get_fixtures_by_date,
    get_league_standings,
    get_next_fixtures_by_team_id,
    get_team_id_by_name
)
from src.db.database import add_favorite, get_favorites
from src.services.ai_service import analyze_match

router = Router()

# ---------------- TEMP CACHE FOR MATCHES ----------------
MATCH_CACHE = {}

# ---------------- START ----------------
@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "👋 Привет! Я футбольный ассистент.\nВыбери действие 👇",
        reply_markup=menu_keyboard
    )

# ---------------- MENUS ----------------
menu_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⚽ Матчи сегодня", callback_data="today")],
        [InlineKeyboardButton(text="📅 Матчи по дате", callback_data="date")],
        [InlineKeyboardButton(text="🏆 Таблицы лиг", callback_data="standings")],
        [InlineKeyboardButton(text="⭐ Избранные команды", callback_data="favorites")],
        [InlineKeyboardButton(text="⭐ Матчи избранных", callback_data="fav_matches")],
    ]
)

date_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Сегодня", callback_data="date_today"),
            InlineKeyboardButton(text="⏭ Завтра", callback_data="date_tomorrow"),
        ],
        [InlineKeyboardButton(text="🗓 Ввести дату", callback_data="date_manual")],
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

# ---------------- TODAY MATCHES ----------------
@router.callback_query(lambda c: c.data == "today")
async def today_matches(callback):
    fixtures = get_today_fixtures()

    if not fixtures:
        await callback.message.answer("Сегодня матчей не найдено ⚽")
        return

    for match in fixtures[:5]:
        match_id = str(uuid.uuid4())[:8]

        MATCH_CACHE[match_id] = {
            "home": match["teams"]["home"]["name"],
            "away": match["teams"]["away"]["name"],
            "league": match["league"]["name"],
            "date": match["fixture"]["date"][:16].replace("T", " ")
        }

        text = (
            f"🏟 {MATCH_CACHE[match_id]['league']}\n"
            f"{MATCH_CACHE[match_id]['home']} vs {MATCH_CACHE[match_id]['away']}\n"
            f"🕒 {MATCH_CACHE[match_id]['date']}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🤖 Анализ матча",
                        callback_data=f"analyze:{match_id}"
                    )
                ]
            ]
        )

        await callback.message.answer(text, reply_markup=keyboard)

# ---------------- DATE MATCHES ----------------
@router.callback_query(lambda c: c.data == "date")
async def date_menu(callback):
    await callback.message.answer("📅 Выбери дату:", reply_markup=date_keyboard)

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
    await callback.message.answer("Введи дату:\n/date YYYY-MM-DD")

async def send_matches_by_date(callback, date: str):
    fixtures = get_fixtures_by_date(date)

    if not fixtures:
        await callback.message.answer(f"На {date} матчей не найдено ⚽")
        return

    for match in fixtures[:5]:
        match_id = str(uuid.uuid4())[:8]

        MATCH_CACHE[match_id] = {
            "home": match["teams"]["home"]["name"],
            "away": match["teams"]["away"]["name"],
            "league": match["league"]["name"],
            "date": match["fixture"]["date"][:16].replace("T", " ")
        }

        text = (
            f"🏟 {MATCH_CACHE[match_id]['league']}\n"
            f"{MATCH_CACHE[match_id]['home']} vs {MATCH_CACHE[match_id]['away']}\n"
            f"🕒 {MATCH_CACHE[match_id]['date']}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🤖 Анализ матча",
                        callback_data=f"analyze:{match_id}"
                    )
                ]
            ]
        )

        await callback.message.answer(text, reply_markup=keyboard)

# ---------------- FAVORITES ----------------
@router.message(lambda msg: msg.text.startswith("/fav"))
async def add_favorite_handler(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Используй:\n/fav TEAM_NAME")
        return

    team_name = parts[1]
    team_id = get_team_id_by_name(team_name)

    if not team_id:
        await message.answer("⚠️ Команда не найдена.")
        return

    add_favorite(message.from_user.id, team_id, team_name)
    await message.answer(f"⭐ {team_name} добавлена в избранное!")

@router.callback_query(lambda c: c.data == "favorites")
async def show_favorites(callback):
    favorites = get_favorites(callback.from_user.id)
    if not favorites:
        await callback.message.answer("⭐ У тебя нет избранных команд.")
        return

    text = "⭐ Твои избранные команды:\n\n"
    for _, team_name in favorites:
        text += f"• {team_name}\n"

    await callback.message.answer(text)

@router.callback_query(lambda c: c.data == "fav_matches")
async def favorite_matches(callback):
    favorites = get_favorites(callback.from_user.id)

    if not favorites:
        await callback.message.answer("⭐ У тебя нет избранных команд.")
        return

    found = False

    for team_id, team_name in favorites:
        fixtures = get_next_fixtures_by_team_id(team_id)

        if not fixtures:
            await callback.message.answer(
                f"⚠️ Нет ближайших матчей для {team_name}"
            )
            continue

        found = True
        match = fixtures[0]
        match_id = str(uuid.uuid4())[:8]

        MATCH_CACHE[match_id] = {
            "home": match["teams"]["home"]["name"],
            "away": match["teams"]["away"]["name"],
            "league": match["league"]["name"],
            "date": match["fixture"]["date"][:16].replace("T", " ")
        }

        text = (
            f"🏟 {MATCH_CACHE[match_id]['league']}\n"
            f"{MATCH_CACHE[match_id]['home']} vs {MATCH_CACHE[match_id]['away']}\n"
            f"🕒 {MATCH_CACHE[match_id]['date']}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🤖 Анализ матча",
                        callback_data=f"analyze:{match_id}"
                    )
                ]
            ]
        )

        await callback.message.answer(text, reply_markup=keyboard)

    if not found:
        await callback.message.answer(
            "⚠️ Для избранных команд нет ближайших матчей."
        )

# ---------------- STANDINGS ----------------
@router.callback_query(lambda c: c.data == "standings")
async def standings_menu(callback):
    await callback.message.answer("🏆 Выбери лигу:", reply_markup=standings_keyboard)

@router.callback_query(lambda c: c.data == "pl")
async def pl(callback): await send_standings(callback, 39, "Premier League")

@router.callback_query(lambda c: c.data == "laliga")
async def laliga(callback): await send_standings(callback, 140, "La Liga")

@router.callback_query(lambda c: c.data == "seriea")
async def seriea(callback): await send_standings(callback, 135, "Serie A")

@router.callback_query(lambda c: c.data == "bundesliga")
async def bundesliga(callback): await send_standings(callback, 78, "Bundesliga")

async def send_standings(callback, league_id: int, title: str):
    standings = get_league_standings(league_id)
    if not standings:
        await callback.message.answer("Таблица недоступна ⚠️")
        return

    text = f"🏆 {title} (Top 5)\n\n"
    for team in standings[:5]:
        text += f"{team['rank']}. {team['team']['name']} — {team['points']} pts\n"

    await callback.message.answer(text)

# ---------------- AI ANALYSIS ----------------
@router.callback_query(lambda c: c.data.startswith("analyze:"))
async def analyze_callback(callback):
    match_id = callback.data.split(":")[1]
    match = MATCH_CACHE.get(match_id)

    if not match:
        await callback.message.answer("⚠️ Данные матча устарели.")
        return

    await callback.message.answer("🤖 Анализирую матч...")

    try:
        analysis = analyze_match(
            match["home"],
            match["away"],
            match["league"],
            match["date"]
        )
        await callback.message.answer(f"🤖 Анализ матча\n\n{analysis}")
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка анализа:\n{e}")

