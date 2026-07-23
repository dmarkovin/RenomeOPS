import asyncio


from aiogram import Bot, Dispatcher


from app.config import BOT_TOKEN


from app.database import (
    connect_db,
    close_db
)


from app.services.bootstrap import create_first_admin


from app.handlers.start import router as start_router

from app.handlers.admin.employees import router as employees_router



async def main():


    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is not set"
        )


    await connect_db()


    await create_first_admin()


    bot = Bot(
        token=BOT_TOKEN
    )


    dp = Dispatcher()


    dp.include_router(
        start_router
    )


    dp.include_router(
        employees_router
    )


    print(
        "Renome OPS Bot started"
    )


    try:

        await dp.start_polling(bot)

    finally:

        await close_db()



if __name__ == "__main__":

    asyncio.run(main())
