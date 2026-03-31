import sys
from contextlib import asynccontextmanager
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.bot.runtime import BotRuntime
from src.config.settings import TELEGRAM_BOT_TOKEN, WEBAPP_HOST, WEBAPP_PORT
from src.core.container import ServiceContainer, build_service_container
from src.infrastructure.football_api_client import FootballApiError
from src.services.match_service import MatchService
from src.web.presenters import serialize_favorites, serialize_match, serialize_matches

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_web_app(services: ServiceContainer | None = None):
    owned_container = services is None
    state = {"services": services, "bot_runtime": None}

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if state["services"] is None:
            state["services"] = build_service_container(include_analysis=True)

        app.state.services = state["services"]
        app.state.services.logger.info("Mini app backend ready")

        if TELEGRAM_BOT_TOKEN and all(
            hasattr(app.state.services, attr)
            for attr in (
                "notification_repository",
                "reminder_log_repository",
                "favorites_service",
                "users_repository",
                "search_service",
            )
        ):
            state["bot_runtime"] = BotRuntime(app.state.services)
            await state["bot_runtime"].start()
            app.state.bot_runtime = state["bot_runtime"]

        try:
            yield
        finally:
            if state["bot_runtime"] is not None:
                await state["bot_runtime"].stop()
            if owned_container and app.state.services is not None:
                await app.state.services.aclose()

    app = FastAPI(title="Football Assistant WebApp", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.exception_handler(FootballApiError)
    async def football_api_error_handler(_, exc: FootballApiError):
        return JSONResponse(
            status_code=503,
            content={
                "error": exc.user_message,
                "details": exc.details,
            },
        )

    @app.get("/")
    async def root():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/api/health")
    async def api_health():
        return {"ok": True}

    @app.get("/api/leagues")
    async def leagues():
        return {"leagues": MatchService.supported_leagues()}

    def resolve_league(league_id: int | None = None):
        leagues = MatchService.supported_leagues()
        if league_id is None:
            return leagues[0]
        for league in leagues:
            if league["id"] == league_id:
                return league
        return leagues[0]

    @app.get("/api/today")
    async def today(league_id: int | None = Query(default=None)):
        match_service = app.state.services.match_service
        matches = await match_service.get_today_matches()
        if league_id is not None:
            matches = match_service.filter_matches_by_league(matches, league_id=league_id)
        return {"matches": serialize_matches(matches)}

    @app.get("/api/live")
    async def live():
        matches = await app.state.services.match_service.get_live_matches()
        return {"matches": serialize_matches(matches)}

    @app.get("/live")
    async def live_alias():
        matches = await app.state.services.match_service.get_live_matches()
        return {"items": serialize_matches(matches)}

    @app.get("/matches")
    async def matches():
        matches_data = await app.state.services.match_service.get_upcoming_matches(limit=12)
        return {"items": serialize_matches(matches_data)}

    @app.get("/standings")
    async def standings(league_id: int | None = Query(default=None)):
        league = resolve_league(league_id)
        rows = await app.state.services.match_service.get_standings(league["name"])
        return {"league": league, "items": rows}

    @app.get("/api/match/{match_id}")
    async def match_details(match_id: int):
        match = await app.state.services.match_service.get_match(match_id)
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        return {"match": serialize_match(match)}

    @app.get("/api/match/{match_id}/events")
    async def match_events(match_id: int):
        return {"events": await app.state.services.match_service.get_match_events(match_id)}

    @app.get("/api/match/{match_id}/statistics")
    async def match_statistics(match_id: int):
        return {"statistics": await app.state.services.match_service.get_match_statistics(match_id)}

    @app.get("/api/match/{match_id}/lineups")
    async def match_lineups(match_id: int):
        return {"lineups": await app.state.services.match_service.get_match_lineups(match_id)}

    @app.get("/api/match/{match_id}/players")
    async def match_players(match_id: int):
        return {"players": await app.state.services.match_service.get_match_players(match_id)}

    @app.get("/api/favorites/{user_id}")
    async def favorites(user_id: int):
        favorites_data = await app.state.services.favorites_service.get_user_favorites_overview(user_id)
        return {"favorites": serialize_favorites(favorites_data)}

    return app


app = create_web_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.web.app:app", host=WEBAPP_HOST, port=WEBAPP_PORT, reload=False)
