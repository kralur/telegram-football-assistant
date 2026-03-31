import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.settings import TELEGRAM_BOT_TOKEN
from src.core.container import build_service_container
from src.bot.runtime import BotRuntime


async def main():
    services = build_service_container(include_analysis=True)
    logger = services.logger
    logger.info("Starting Football Assistant...")
    logger.info("Database initialized")

    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is missing")
    runtime = BotRuntime(services)

    try:
        await runtime.start()
        if runtime.polling_task is not None:
            await runtime.polling_task
    finally:
        await runtime.stop()
        await services.aclose()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
