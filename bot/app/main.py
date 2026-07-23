import asyncio


from aiogram import Bot, Dispatcher


from app.config import BOT_TOKEN


from app.database import (
    connect_db,
    close_db
)


# Основные роутеры

from app.handlers.start import router as start_router

from app.handlers.menu import router as menu_router

from app.handlers.admin.employees import router as employees_router

from app.handlers.concierge.reports import router as concierge_reports_router



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



    # Стартовый обработчик

    dp.include_router(
        start_router
    )



    # Авторизация и меню пользователей

    dp.include_router(
        menu_router
    )



    # Администрация - сотрудники

    dp.include_router(
        employees_router
    )



    # Консьерж - отчеты

    dp.include_router(
        concierge_reports_router
    )



    print(
        "Renome OPS Bot started"
    )



    try:

        await dp.start_polling(
            bot
        )


    finally:

        await close_db()



if __name__ == "__main__":

    asyncio.run(main())
