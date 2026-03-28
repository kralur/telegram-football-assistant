import asyncio
from aiogram import Bot, Dispatcher

from src.config.settings import TELEGRAM_BOT_TOKEN
from src.core.logger import setup_logger

from src.infrastructure.football_api_client import FootballApiClient
from src.infrastructure.openai_client import OpenAIClient
from src.infrastructure.cache import TTLCache

from src.services.match_service import MatchService
from src.services.favorites_service import FavoritesService
from src.services.analysis_service import AnalysisService
from src.services.scheduler_service import SchedulerService

from src.db.database import init_db
from src.db.repositories.favorites_repository import FavoritesRepository
from src.db.repositories.users_repository import UsersRepository

from src.bot.handlers import setup_handlers


async def main():
    logger = setup_logger()
    logger.info("Starting Football Assistant...")

    # ==========================
    # DATABASE
    # ==========================
    init_db()
    logger.info("Database initialized")

    # ==========================
    # INFRASTRUCTURE
    # ==========================
    football_client = FootballApiClient()
    openai_client = OpenAIClient()
    cache = TTLCache()

    # ==========================
    # REPOSITORIES
    # ==========================
    favorites_repository = FavoritesRepository()
    users_repository = UsersRepository()

    # ==========================
    # SERVICES
    # ==========================
    match_service = MatchService(football_client, cache)
    favorites_service = FavoritesService(favorites_repository)
    analysis_service = AnalysisService(openai_client)

    # ==========================
    # TELEGRAM BOT
    # ==========================
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is missing")

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    # ==========================
    # ROUTER
    # ==========================
    router = setup_handlers(
        match_service,
        favorites_service,
        analysis_service,
        users_repository
    )

    dp.include_router(router)

    # ==========================
    # SCHEDULER
    # ==========================
    scheduler_service = SchedulerService(
        bot,
        match_service,
        users_repository,
        favorites_repository
    )

    scheduler_service.start()
    logger.info("Scheduler started")

    # ==========================
    # START POLLING
    # ==========================
    logger.info("Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())