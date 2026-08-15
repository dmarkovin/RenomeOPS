import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import TelegramObject
from prometheus_client import start_http_server

from app.config import settings
from app.database.db import init_db, close_db
from app.handlers import routers
from app.middlewares.db import DatabaseMiddleware
from app.middlewares.auth import AuthMiddleware
from app.middlewares.metrics import MetricsMiddleware
from app.metrics import update_uptime, update_business_metrics
from app.services.notification_service import set_bot
from app.services.bootstrap import create_first_admin

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

dp = Dispatcher()

dp.update.middleware(DatabaseMiddleware())
dp.update.middleware(AuthMiddleware())
dp.update.middleware(MetricsMiddleware())

for router in routers:
    dp.include_router(router)

@dp.errors()
async def global_error_handler(update: TelegramObject, exception: Exception):
    logger.error(f"Global error: {exception}", exc_info=True)
    return True

async def main():
    logger.info("Initializing database...")
    await init_db()
    await create_first_admin()
    logger.info("Database initialized.")
    logger.info("All routers registered successfully.")
    logger.info("Renome OPS bot started polling...")

    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    set_bot(bot)

    start_http_server(8000)
    logger.info("Metrics server started on port 8000")

    async def background_metrics():
        while True:
            update_uptime()
            await update_business_metrics()
            await asyncio.sleep(60)
    asyncio.create_task(background_metrics())

    try:
        await dp.start_polling(bot)
    finally:
        logger.info("Shutting down...")
        await close_db()
        await bot.session.close()
        logger.info("Bot stopped gracefully.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
