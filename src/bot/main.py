import asyncio
from aiogram import Bot, Dispatcher

from src.config.settings import TELEGRAM_BOT_TOKEN
from src.bot.handlers import router
from src.db.database import init_db


async def main():
    # ✅ ИНИЦИАЛИЗАЦИЯ БАЗЫ
    init_db()

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    print("🤖 Bot started successfully")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
