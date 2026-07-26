import asyncio

from aiogram import Bot, Dispatcher

from app.config import settings

from app.database import (
    init_db,
    close_db,
)

from app.handlers.start import router as start_router
from app.handlers.menu import router as menu_router

# сотрудники
from app.handlers.employees.admin import (
    router as employees_admin_router
)

from app.handlers.employees.create import (
    router as employees_create_router
)


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


    # =====================
    # ROUTERS
    # =====================

    dp.include_router(
        start_router
    )

    dp.include_router(
        menu_router
    )

    # админ сотрудники
    dp.include_router(
        employees_admin_router
    )

    # создание сотрудника
    dp.include_router(
        employees_create_router
    )


    print("ROUTERS READY")
    print("Renome OPS started")


    try:

        await dp.start_polling(
            bot
        )


    finally:

        await close_db()



if __name__ == "__main__":

    asyncio.run(main())
