import asyncio
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiogram import Bot, Dispatcher

from src.bot.handlers import setup_handlers
from src.config.settings import TELEGRAM_BOT_TOKEN
from src.core.container import (
    build_notify_service,
    build_scheduler_service,
    build_service_container,
)


async def main():
    services = build_service_container(include_analysis=True)
    logger = services.logger
    logger.info("Starting Football Assistant...")
    logger.info("Database initialized")

    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is missing")
    if services.analysis_service is None:
        raise ValueError("OPENAI_API_KEY is missing")

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    notify_service = build_notify_service(services, bot)

    router = setup_handlers(
        match_service=services.match_service,
        analysis_service=services.analysis_service,
        favorites_service=services.favorites_service,
        search_service=services.search_service,
        users_repository=services.users_repository,
        notify_service=notify_service,
    )
    dp.include_router(router)

    scheduler_service = build_scheduler_service(services, bot, notify_service)

    try:
        scheduler_service.start()
        logger.info("Scheduler started")

        logger.info("Bot is running...")
        await dp.start_polling(bot)
    finally:
        await services.aclose()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
