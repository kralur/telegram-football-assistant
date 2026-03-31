import asyncio
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiogram import Bot, Dispatcher

from src.bot.handlers import setup_handlers
from src.config.settings import TELEGRAM_BOT_TOKEN
from src.core.logger import setup_logger
from src.db.database import init_db
from src.db.repositories.favorites_repository import FavoritesRepository
from src.db.repositories.notification_repository import NotificationRepository
from src.db.repositories.reminder_log_repository import ReminderLogRepository
from src.db.repositories.users_repository import UsersRepository
from src.infrastructure.cache import TTLCache
from src.infrastructure.football_api_client import FootballApiClient
from src.infrastructure.openai_client import OpenAIClient
from src.services.analysis_service import AnalysisService
from src.services.favorites_service import FavoritesService
from src.services.match_service import MatchService
from src.services.notify_service import NotifyService
from src.services.scheduler_service import SchedulerService
from src.services.search_service import SearchService


async def main():
    logger = setup_logger()
    logger.info("Starting Football Assistant...")

    init_db()
    logger.info("Database initialized")

    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is missing")

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    cache = TTLCache()
    football_client = FootballApiClient()
    openai_client = OpenAIClient()

    users_repository = UsersRepository()
    favorites_repository = FavoritesRepository()
    notification_repository = NotificationRepository()
    reminder_log_repository = ReminderLogRepository()

    match_service = MatchService(football_client, cache)
    analysis_service = AnalysisService(openai_client, cache)
    favorites_service = FavoritesService(favorites_repository, match_service)
    search_service = SearchService(match_service, cache)
    notify_service = NotifyService(
        notification_repository,
        reminder_log_repository,
        favorites_service,
        match_service,
        users_repository,
        bot,
    )

    router = setup_handlers(
        match_service=match_service,
        analysis_service=analysis_service,
        favorites_service=favorites_service,
        search_service=search_service,
        users_repository=users_repository,
        notify_service=notify_service,
    )
    dp.include_router(router)

    scheduler_service = SchedulerService(
        bot=bot,
        match_service=match_service,
        users_repository=users_repository,
        notify_service=notify_service,
    )

    try:
        scheduler_service.start()
        logger.info("Scheduler started")

        logger.info("Bot is running...")
        await dp.start_polling(bot)
    finally:
        await football_client.aclose()
        await openai_client.client.aclose()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
