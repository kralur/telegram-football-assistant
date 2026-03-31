import asyncio
import logging

from aiogram import Bot, Dispatcher

from src.bot.handlers import setup_handlers
from src.config.settings import TELEGRAM_BOT_TOKEN
from src.core.container import build_notify_service, build_scheduler_service


class BotRuntime:
    def __init__(self, services):
        self.services = services
        self.logger = logging.getLogger("football_bot")
        self.bot: Bot | None = None
        self.dispatcher: Dispatcher | None = None
        self.notify_service = None
        self.scheduler_service = None
        self.polling_task: asyncio.Task | None = None

    @property
    def is_configured(self):
        return bool(TELEGRAM_BOT_TOKEN)

    async def start(self):
        if not self.is_configured:
            self.logger.warning("Telegram bot token is missing; bot runtime was skipped")
            return False

        if self.bot is not None:
            return True

        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.dispatcher = Dispatcher()
        self.notify_service = build_notify_service(self.services, self.bot)

        router = setup_handlers(
            match_service=self.services.match_service,
            analysis_service=self.services.analysis_service,
            favorites_service=self.services.favorites_service,
            search_service=self.services.search_service,
            users_repository=self.services.users_repository,
            notify_service=self.notify_service,
        )
        self.dispatcher.include_router(router)

        self.scheduler_service = build_scheduler_service(
            self.services,
            self.bot,
            self.notify_service,
        )
        self.scheduler_service.start()
        self.logger.info("Scheduler started")

        self.polling_task = asyncio.create_task(
            self.dispatcher.start_polling(self.bot, handle_signals=False)
        )
        self.logger.info("Bot is running...")
        return True

    async def stop(self):
        if self.scheduler_service is not None:
            self.scheduler_service.stop()

        if self.dispatcher is not None and self.polling_task is not None and not self.polling_task.done():
            await self.dispatcher.stop_polling()
            try:
                await self.polling_task
            except Exception as exc:
                self.logger.debug("Bot polling stopped with exception: %s", exc)

        if self.bot is not None:
            await self.bot.session.close()

        self.polling_task = None
        self.scheduler_service = None
        self.notify_service = None
        self.dispatcher = None
        self.bot = None
