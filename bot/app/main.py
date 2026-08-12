import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from app.config import settings
from app.database.db import init_db
from app.handlers import routers
from app.middlewares.db import DatabaseMiddleware
from app.middlewares.auth import AuthMiddleware
from app.services.notification_service import set_bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()

# Регистрация middleware
dp.update.middleware(DatabaseMiddleware())
dp.update.middleware(AuthMiddleware())

# Подключение всех роутеров
for router in routers:
    dp.include_router(router)

async def main():
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized.")
    logger.info("All routers registered successfully.")
    logger.info("Renome OPS bot started polling...")
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    # Инициализируем глобальный bot для уведомлений
    set_bot(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped.")
