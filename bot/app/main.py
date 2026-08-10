import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from app.config import settings
from app.database.db import init_db, close_db
from app.middlewares.db import DatabaseMiddleware
from app.middlewares.auth import AuthMiddleware
from app.handlers import routers

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
    # Создаём бота с токеном из настроек
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped.")
    finally:
        asyncio.run(close_db())
