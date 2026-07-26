import asyncio
import logging

from aiogram import Bot
from aiogram import Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from app.config import settings
from app.handlers import routers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


async def main():

    bot = Bot(

        token=settings.BOT_TOKEN,

        default=DefaultBotProperties(

            parse_mode=ParseMode.HTML

        )

    )

    dp = Dispatcher()

    for router in routers:

        dp.include_router(router)

    logging.info("Renome OPS started")

    await dp.start_polling(bot)


if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        logging.info("Bot stopped")
