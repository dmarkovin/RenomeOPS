import asyncio

from aiogram import Bot, Dispatcher

from app.config import settings

from app.database import (
    init_db,
    close_db,
)

from app.handlers.start import router as start_router
from app.handlers.menu import router as menu_router

from app.middlewares.db import DatabaseMiddleware


async def main():

    print("CALL INIT DATABASE")

    await init_db()

    bot = Bot(
        token=settings.BOT_TOKEN
    )

    dp = Dispatcher()


    dp.update.middleware(
        DatabaseMiddleware()
    )


    dp.include_router(start_router)
    dp.include_router(menu_router)


    print("ROUTERS READY")
    print("Renome OPS started")


    try:

        await dp.start_polling(bot)


    finally:

        await close_db()



if __name__ == "__main__":

    asyncio.run(main())
