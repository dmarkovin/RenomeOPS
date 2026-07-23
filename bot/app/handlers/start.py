from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command


from app.services.employee_service import get_employee


from app.keyboards.admin import admin_keyboard
from app.keyboards.concierge import concierge_keyboard
from app.keyboards.director import director_keyboard
from app.keyboards.executor import executor_keyboard



router = Router()



@router.message(Command("start"))
async def start_handler(
    message: Message
):

    telegram_id = message.from_user.id


    employee = await get_employee(
        telegram_id
    )


    if not employee:

        await message.answer(
            """
👋 Добро пожаловать в Renome OPS!

Ваш аккаунт еще не зарегистрирован.

Обратитесь к администратору.
"""
        )

        return



    role = employee["role"]



    if role == "SUPER_ADMIN":

        keyboard = admin_keyboard()

        text = """
👑 Администратор Renome OPS

Полный доступ к системе.
"""



    elif role == "CONCIERGE":

        keyboard = concierge_keyboard()

        text = """
🛎 Консьерж Renome OPS

Рабочее меню ресепшен.
"""



    elif role == "DIRECTOR":

        keyboard = director_keyboard()

        text = """
👨‍💼 Начальник объекта

Контроль и аналитика.
"""



    elif role in (
        "EXECUTOR",
        "TEAM_TECH",
        "TEAM_CLEANING",
        "TEAM_SECURITY"
    ):

        keyboard = executor_keyboard()

        text = """
🔧 Исполнитель

Ваши рабочие задачи.
"""



    else:

        keyboard = None

        text = """
⚠️ Роль пользователя не определена.
"""



    await message.answer(
        text,
        reply_markup=keyboard
    )
