import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from src.bot.keyboards import (
    TIMEZONE_OPTIONS,
    back_keyboard,
    favorites_keyboard,
    league_picker_keyboard,
    main_menu_keyboard,
    match_card_keyboard,
    match_detail_keyboard,
    search_results_keyboard,
    table_screen_keyboard,
    today_filter_keyboard,
    timezone_keyboard,
)
from src.bot.pagination import paginate
from src.bot.session_store import SessionStore
from src.bot.views import (
    favorites_text,
    help_text,
    analysis_text,
    main_menu_text,
    match_card_text,
    match_details_text,
    match_events_text,
    match_lineups_text,
    match_players_text,
    match_statistics_text,
    notification_added_text,
    notification_unavailable_text,
    scorers_text,
    search_prompt_text,
    search_results_text,
    service_error_text,
    standings_text,
    timezone_text,
)
from src.infrastructure.football_api_client import FootballApiError

router = Router()
services = {}
sessions = SessionStore()
logger = logging.getLogger("football_bot")

MATCHES_PAGE_SIZE = 5
MATCH_CARD_PAGE_SIZE = 1
TABLE_PAGE_SIZE = 10
SEARCH_PAGE_SIZE = 5
FAVORITES_PAGE_SIZE = 4


def setup_handlers(
    match_service,
    analysis_service,
    favorites_service,
    search_service,
    users_repository,
    notify_service,
):
    services["match_service"] = match_service
    services["analysis_service"] = analysis_service
    services["favorites_service"] = favorites_service
    services["search_service"] = search_service
    services["users_repository"] = users_repository
    services["notify_service"] = notify_service
    return router


def ensure_user(event):
    user_id = event.from_user.id
    services["users_repository"].add(user_id)
    sessions.ensure(user_id)
    return user_id


def user_timezone(user_id: int):
    return services["users_repository"].get_timezone(user_id)


def league_by_id(league_id: int):
    for league in services["match_service"].supported_leagues():
        if league["id"] == league_id:
            return league
    return services["match_service"].supported_leagues()[0]


async def render_message(message: Message, user_id: int):
    user_label = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else message.from_user.full_name
    )
    cleanup_message = await message.answer(
        "Switching to inline mode...",
        reply_markup=ReplyKeyboardRemove(),
    )
    try:
        await cleanup_message.delete()
    except Exception:
        logger.debug("Could not delete inline cleanup message for user=%s", user_id)

    sent = await message.answer(
        main_menu_text(user_timezone(user_id), user_label=user_label),
        reply_markup=main_menu_keyboard(),
    )
    sessions.set_anchor(user_id, sent.message_id)
    sessions.replace_screen(user_id, "main", {})


async def render_anchor(user_id: int, bot, chat_id: int, screen: str, payload: dict | None = None, push: bool = True):
    payload = payload or {}
    if push:
        sessions.set_screen(user_id, screen, payload=payload)
    else:
        sessions.replace_screen(user_id, screen, payload=payload)

    try:
        text, markup, actual_payload = await build_screen(user_id, screen, payload)
    except FootballApiError as exc:
        logger.warning(
            "Failed to build screen for user=%s screen=%s: %s",
            user_id,
            screen,
            exc.details,
        )
        text = service_error_text(exc.user_message)
        markup = back_keyboard()
        actual_payload = payload
    sessions.replace_screen(user_id, screen, payload=actual_payload)

    anchor_id = sessions.get_anchor(user_id)
    if anchor_id is None:
        sent = await bot.send_message(chat_id, text, reply_markup=markup)
        sessions.set_anchor(user_id, sent.message_id)
        return

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=anchor_id,
            text=text,
            reply_markup=markup,
        )
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            logger.debug(
                "Skipped identical message update for user=%s screen=%s",
                user_id,
                screen,
            )
            return
        raise


async def render_callback(call: CallbackQuery, screen: str, payload: dict | None = None, push: bool = True):
    user_id = ensure_user(call)
    sessions.set_anchor(user_id, call.message.message_id)
    await render_anchor(
        user_id=user_id,
        bot=call.bot,
        chat_id=call.message.chat.id,
        screen=screen,
        payload=payload,
        push=push,
    )


async def build_screen(user_id: int, screen: str, payload: dict):
    timezone = user_timezone(user_id)

    if screen == "main":
        return main_menu_text(timezone), main_menu_keyboard(), {}

    if screen == "service_error":
        return service_error_text(payload.get("message", "Football data is temporarily unavailable.")), back_keyboard(), payload

    if screen == "help":
        return help_text(), back_keyboard(), payload

    if screen == "today":
        matches = payload.get("matches")
        if matches is None:
            matches = await services["match_service"].get_today_matches()
        selected_league_id = payload.get("league_id")
        selected_league_name = payload.get("league_name", "All leagues")
        filtered_matches = services["match_service"].filter_matches_by_league(matches, selected_league_id)
        page_items, page, total_pages = paginate(filtered_matches, payload.get("page", 0), MATCH_CARD_PAGE_SIZE)
        current_match = page_items[0] if page_items else None
        title = "Today's matches" if selected_league_id is None else f"Today's matches - {selected_league_name}"
        return (
            match_card_text(title, current_match, timezone, page, total_pages),
            match_card_keyboard(current_match, page, total_pages),
            {
                "matches": matches,
                "page": page,
                "league_id": selected_league_id,
                "league_name": selected_league_name,
            },
        )

    if screen == "today_filter":
        selected_league_id = payload.get("league_id")
        return (
            "Filter today's matches by league.",
            today_filter_keyboard(
                services["match_service"].supported_leagues(),
                selected_league_id=selected_league_id,
            ),
            payload,
        )

    if screen == "live":
        matches = payload.get("matches")
        if matches is None:
            matches = await services["match_service"].get_live_matches()
        page_items, page, total_pages = paginate(matches, payload.get("page", 0), MATCH_CARD_PAGE_SIZE)
        current_match = page_items[0] if page_items else None
        return (
            match_card_text("Live matches", current_match, timezone, page, total_pages),
            match_card_keyboard(current_match, page, total_pages),
            {"matches": matches, "page": page},
        )

    if screen == "standings_leagues":
        leagues = services["match_service"].supported_leagues()
        return "Choose a league for standings.", league_picker_keyboard(leagues, "league:standings"), payload

    if screen == "scorers_leagues":
        leagues = services["match_service"].supported_leagues()
        return "Choose a league for top scorers.", league_picker_keyboard(leagues, "league:scorers"), payload

    if screen == "standings":
        league = payload["league"]
        rows = payload.get("rows")
        if rows is None:
            rows = await services["match_service"].get_standings(league["name"])
        page_items, page, total_pages = paginate(rows, payload.get("page", 0), TABLE_PAGE_SIZE)
        return (
            standings_text(league["name"], page_items, page, total_pages),
            table_screen_keyboard(page, total_pages),
            {"league": league, "rows": rows, "page": page},
        )

    if screen == "scorers":
        league = payload["league"]
        rows = payload.get("rows")
        if rows is None:
            rows = await services["match_service"].get_top_scorers(league["name"])
        page_items, page, total_pages = paginate(rows, payload.get("page", 0), TABLE_PAGE_SIZE)
        return (
            scorers_text(league["name"], page_items, page, total_pages),
            table_screen_keyboard(page, total_pages),
            {"league": league, "rows": rows, "page": page},
        )

    if screen == "search_prompt":
        return search_prompt_text(), back_keyboard(), payload

    if screen == "search_results":
        query = payload.get("query", "")
        results = payload.get("results", [])
        page_items, page, total_pages = paginate(results, payload.get("page", 0), SEARCH_PAGE_SIZE)
        offset = page * SEARCH_PAGE_SIZE
        return (
            search_results_text(query, page_items, page, total_pages),
            search_results_keyboard(page_items, page, total_pages, offset=offset),
            {"query": query, "results": results, "page": page},
        )

    if screen == "favorites":
        favorites = payload.get("favorites")
        if favorites is None:
            favorites = await services["favorites_service"].get_user_favorites_overview(user_id)
        pending = services["notify_service"].list_pending_notifications(user_id)
        page_items, page, total_pages = paginate(favorites, payload.get("page", 0), FAVORITES_PAGE_SIZE)
        offset = page * FAVORITES_PAGE_SIZE
        return (
            favorites_text(page_items, len(pending), timezone, page, total_pages),
            favorites_keyboard(page_items, page, total_pages, offset=offset),
            {"favorites": favorites, "page": page},
        )

    if screen == "timezone":
        return timezone_text(timezone), timezone_keyboard(timezone), payload

    if screen == "notification_added":
        match = payload["match"]
        return notification_added_text(match, timezone), back_keyboard(), payload

    if screen == "notification_unavailable":
        return notification_unavailable_text(), back_keyboard(), payload

    if screen == "match_details":
        match = payload["match"]
        return (
            match_details_text(match, timezone),
            match_detail_keyboard(match["id"], active="summary"),
            payload,
        )

    if screen == "match_events":
        match = payload["match"]
        events = payload.get("events")
        if events is None:
            events = await services["match_service"].get_match_events(match["id"])
        return (
            match_events_text(match, events, timezone),
            match_detail_keyboard(match["id"], active="events"),
            {"match": match, "events": events},
        )

    if screen == "match_statistics":
        match = payload["match"]
        statistics = payload.get("statistics")
        if statistics is None:
            statistics = await services["match_service"].get_match_statistics(match["id"])
        return (
            match_statistics_text(match, statistics, timezone),
            match_detail_keyboard(match["id"], active="statistics"),
            {"match": match, "statistics": statistics},
        )

    if screen == "match_lineups":
        match = payload["match"]
        lineups = payload.get("lineups")
        if lineups is None:
            lineups = await services["match_service"].get_match_lineups(match["id"])
        return (
            match_lineups_text(match, lineups, timezone),
            match_detail_keyboard(match["id"], active="lineups"),
            {"match": match, "lineups": lineups},
        )

    if screen == "match_players":
        match = payload["match"]
        players = payload.get("players")
        if players is None:
            players = await services["match_service"].get_match_players(match["id"])
        return (
            match_players_text(match, players, timezone),
            match_detail_keyboard(match["id"], active="players"),
            {"match": match, "players": players},
        )

    if screen == "analysis":
        match = payload["match"]
        analysis = payload["analysis"]
        return (
            analysis_text(match, analysis, timezone),
            match_detail_keyboard(match["id"], active="analysis"),
            payload,
        )

    return main_menu_text(timezone), main_menu_keyboard(), {}


@router.message(CommandStart())
async def start(message: Message):
    user_id = ensure_user(message)
    await render_message(message, user_id)


@router.message(Command("help"))
async def help_command(message: Message):
    user_id = ensure_user(message)
    await render_anchor(
        user_id=user_id,
        bot=message.bot,
        chat_id=message.chat.id,
        screen="help",
        payload={},
        push=True,
    )


@router.callback_query()
async def callback_router(call: CallbackQuery):
    user_id = ensure_user(call)
    action = call.data or ""
    screen = sessions.current_screen(user_id)
    payload = sessions.current_payload(user_id)

    if action == "noop":
        await call.answer()
        return

    await call.answer()

    try:
        if action == "nav:today":
            await render_callback(call, "today")
        elif action == "nav:live":
            await render_callback(call, "live")
        elif action == "nav:today_filter":
            await render_callback(
                call,
                "today_filter",
                {
                    "matches": payload.get("matches"),
                    "league_id": payload.get("league_id"),
                    "league_name": payload.get("league_name", "All leagues"),
                    "page": payload.get("page", 0),
                },
            )
        elif action == "nav:standings_leagues":
            await render_callback(call, "standings_leagues")
        elif action == "nav:scorers_leagues":
            await render_callback(call, "scorers_leagues")
        elif action == "nav:search":
            await render_callback(call, "search_prompt")
        elif action == "nav:favorites":
            await render_callback(call, "favorites")
        elif action == "nav:timezone":
            await render_callback(call, "timezone")
        elif action == "nav:help":
            await render_callback(call, "help")
        elif action == "nav:main":
            await render_anchor(
                user_id=user_id,
                bot=call.bot,
                chat_id=call.message.chat.id,
                screen="main",
                payload={},
                push=True,
            )
        elif action == "nav:back":
            previous = sessions.back(user_id)
            await render_anchor(
                user_id=user_id,
                bot=call.bot,
                chat_id=call.message.chat.id,
                screen=previous["screen"],
                payload=previous["payload"],
                push=False,
            )
        elif action.startswith("page:"):
            next_page = int(action.split(":")[-1])
            next_payload = dict(payload)
            next_payload["page"] = next_page
            await render_anchor(
                user_id=user_id,
                bot=call.bot,
                chat_id=call.message.chat.id,
                screen=screen,
                payload=next_payload,
                push=False,
            )
        elif action.startswith("league:standings:"):
            league = league_by_id(int(action.split(":")[-1]))
            await render_callback(call, "standings", {"league": league, "page": 0})
        elif action.startswith("league:scorers:"):
            league = league_by_id(int(action.split(":")[-1]))
            await render_callback(call, "scorers", {"league": league, "page": 0})
        elif action == "today_filter:all":
            await render_callback(
                call,
                "today",
                {"matches": payload.get("matches"), "page": 0, "league_id": None, "league_name": "All leagues"},
            )
        elif action.startswith("today_filter:"):
            league = league_by_id(int(action.split(":")[-1]))
            await render_callback(
                call,
                "today",
                {
                    "matches": payload.get("matches"),
                    "page": 0,
                    "league_id": league["id"],
                    "league_name": league["name"],
                },
            )
        elif action.startswith("timezone:set:"):
            timezone_index = int(action.split(":")[-1])
            timezone_value = TIMEZONE_OPTIONS[timezone_index][0]
            services["users_repository"].set_timezone(user_id, timezone_value)
            await render_anchor(
                user_id=user_id,
                bot=call.bot,
                chat_id=call.message.chat.id,
                screen="timezone",
                payload={},
                push=False,
            )
        elif action.startswith("notify:match:"):
            match_id = int(action.split(":")[-1])
            match = await services["notify_service"].subscribe(user_id, match_id)
            if match:
                await render_callback(call, "notification_added", {"match": match})
            else:
                await render_callback(call, "notification_unavailable", {})
        elif action.startswith("match:open:"):
            match_id = int(action.split(":")[-1])
            match = await services["match_service"].get_match(match_id)
            if match:
                await render_callback(call, "match_details", {"match": match})
        elif action.startswith("match:events:"):
            match_id = int(action.split(":")[-1])
            match = payload.get("match") if payload.get("match", {}).get("id") == match_id else None
            if match is None:
                match = await services["match_service"].get_match(match_id)
            if match:
                await render_callback(call, "match_events", {"match": match})
        elif action.startswith("match:statistics:"):
            match_id = int(action.split(":")[-1])
            match = payload.get("match") if payload.get("match", {}).get("id") == match_id else None
            if match is None:
                match = await services["match_service"].get_match(match_id)
            if match:
                await render_callback(call, "match_statistics", {"match": match})
        elif action.startswith("match:lineups:"):
            match_id = int(action.split(":")[-1])
            match = payload.get("match") if payload.get("match", {}).get("id") == match_id else None
            if match is None:
                match = await services["match_service"].get_match(match_id)
            if match:
                await render_callback(call, "match_lineups", {"match": match})
        elif action.startswith("match:players:"):
            match_id = int(action.split(":")[-1])
            match = payload.get("match") if payload.get("match", {}).get("id") == match_id else None
            if match is None:
                match = await services["match_service"].get_match(match_id)
            if match:
                await render_callback(call, "match_players", {"match": match})
        elif action.startswith("analysis:match:"):
            match_id = int(action.split(":")[-1])
            match = payload.get("match") if payload.get("match", {}).get("id") == match_id else None
            if match is None:
                match = await services["match_service"].get_match(match_id)
            if match:
                if services["analysis_service"] is None:
                    raise FootballApiError(
                        "AI analysis is not configured for this deployment.",
                        details="OPENAI_API_KEY is missing",
                    )
                analysis = await services["analysis_service"].analyze(match)
                await render_callback(call, "analysis", {"match": match, "analysis": analysis})
        elif action.startswith("favorite:add:"):
            index = int(action.split(":")[-1])
            results = payload.get("results", [])
            if 0 <= index < len(results):
                team = results[index]
                services["favorites_service"].add_team(
                    user_id=user_id,
                    team_name=team["name"],
                    team_id=team["id"],
                )
                await services["notify_service"].sync_favorites_for_user(user_id)
            await render_callback(call, "favorites")
        elif action.startswith("favorite:remove:"):
            index = int(action.split(":")[-1])
            favorites = payload.get("favorites", [])
            if 0 <= index < len(favorites):
                favorite = favorites[index]
                services["favorites_service"].remove_team(
                    user_id=user_id,
                    team_name=favorite["team_name"],
                    team_id=favorite.get("team_id"),
                )
            await render_callback(call, "favorites")
        elif action.startswith("favorite:open_next:"):
            index = int(action.split(":")[-1])
            favorites = payload.get("favorites", [])
            if 0 <= index < len(favorites):
                favorite = favorites[index]
                next_match = favorite.get("next_match")
                if next_match and next_match.get("id") is not None:
                    match = await services["match_service"].get_match(next_match["id"])
                    await render_callback(call, "match_details", {"match": match or next_match})
        elif action.startswith("favorite:notify_next:"):
            index = int(action.split(":")[-1])
            favorites = payload.get("favorites", [])
            if 0 <= index < len(favorites):
                favorite = favorites[index]
                next_match = favorite.get("next_match")
                if next_match and next_match.get("id") is not None:
                    match = await services["notify_service"].subscribe(user_id, next_match["id"])
                    if match:
                        await render_callback(call, "notification_added", {"match": match})
                    else:
                        await render_callback(call, "notification_unavailable", {})
    except FootballApiError as exc:
        logger.warning(
            "Callback action failed for user=%s action=%s: %s",
            user_id,
            action,
            exc.details,
        )
        await render_anchor(
            user_id=user_id,
            bot=call.bot,
            chat_id=call.message.chat.id,
            screen="service_error",
            payload={"message": exc.user_message},
            push=True,
        )


@router.message()
async def search_input_handler(message: Message):
    user_id = ensure_user(message)
    if sessions.current_screen(user_id) not in {"search_prompt", "search_results"}:
        return

    query = (message.text or "").strip()
    try:
        results = await services["search_service"].search_teams(query)
        await render_anchor(
            user_id=user_id,
            bot=message.bot,
            chat_id=message.chat.id,
            screen="search_results",
            payload={"query": query, "results": results, "page": 0},
            push=True,
        )
    except FootballApiError as exc:
        logger.warning("Search failed for user=%s query=%s: %s", user_id, query, exc.details)
        await render_anchor(
            user_id=user_id,
            bot=message.bot,
            chat_id=message.chat.id,
            screen="service_error",
            payload={"message": exc.user_message},
            push=True,
        )
