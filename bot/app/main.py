import asyncio


from aiogram import Bot, Dispatcher


from app.config import BOT_TOKEN

from app.database import (
    connect_db,
    close_db
)


from app.handlers.start import router as start_router



async def main():


    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is not set"
        )


    await connect_db()


    bot = Bot(
        token=BOT_TOKEN
    )


    dp = Dispatcher()


    dp.include_router(
        start_router
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
