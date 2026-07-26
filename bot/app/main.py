import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings
from app.database import init_db, close_db
from app.middlewares.db import DatabaseMiddleware
from app.services.bootstrap import create_first_admin
from app.services.notification_service import set_bot
from app.handlers import routers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


async def main() -> None:
    logging.info("Initializing database...")
    await init_db()

    logging.info("Creating first admin (if not exists)...")
    await create_first_admin()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Передаём экземпляр бота в сервис уведомлений
    set_bot(bot)

    dp = Dispatcher()

    # Подключаем middleware для сессий БД
    dp.update.middleware(DatabaseMiddleware())

    # Регистрируем все роутеры из единого списка
    for router in routers:
        dp.include_router(router)

    logging.info("All routers registered successfully.")
    logging.info("Renome OPS bot started polling...")

    try:
        await dp.start_polling(bot)
    finally:
        await close_db()
        logging.info("Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
