import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import TelegramObject

from app.config import settings
from app.database.db import init_db, close_db
from app.handlers import routers
from app.middlewares.db import DatabaseMiddleware
from app.middlewares.auth import AuthMiddleware
from app.middlewares.metrics import MetricsMiddleware
from app.metrics import start_http_server, update_uptime, update_business_metrics
from app.services.notification_service import set_bot

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

dp = Dispatcher()

# Регистрация middleware
dp.update.middleware(DatabaseMiddleware())
dp.update.middleware(AuthMiddleware())
dp.update.middleware(MetricsMiddleware())

# Подключение всех роутеров
for router in routers:
    dp.include_router(router)

# Глобальный обработчик ошибок
@dp.errors()
async def global_error_handler(update: TelegramObject, exception: Exception):
    logger.error(f"Global error: {exception}", exc_info=True)
    # Метрика уже инкрементится в MetricsMiddleware
    # Можно добавить уведомление админам при критических ошибках
    return True

async def main():
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized.")
    logger.info("All routers registered successfully.")
    logger.info("Renome OPS bot started polling...")
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    set_bot(bot)
    start_http_server(8000)
    # Фоновое обновление uptime и бизнес-метрик
    async def background_metrics():
        while True:
            update_uptime()
            await update_business_metrics()
            await asyncio.sleep(60)  # раз в минуту
    asyncio.create_task(background_metrics())
    try:
        await dp.start_polling(bot)
    finally:
        await close_db()
        await bot.session.close()
        logger.info("Bot stopped gracefully.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
