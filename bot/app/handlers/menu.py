from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command


from app.services.employee_service import get_employee


from app.keyboards.admin import admin_keyboard
from app.keyboards.director import director_keyboard
from app.keyboards.concierge import concierge_keyboard
from app.keyboards.executor import executor_keyboard



router = Router()



@router.message(Command("menu"))
@router.message(Command("start"))
async def menu_handler(
    message: Message
):


    employee = await get_employee(
        message.from_user.id
    )


    if not employee:

        await message.answer(
            """
⛔ Доступ ограничен


Ваш Telegram не зарегистрирован
в системе Renome OPS.


Обратитесь к администратору.
"""
        )

        return



    role = employee["role"]



    if role == "SUPER_ADMIN":

        keyboard = admin_keyboard()



    elif role == "DIRECTOR":

        keyboard = director_keyboard()



    elif role == "CONCIERGE":

        keyboard = concierge_keyboard()



    elif role in [
        "TECH_SPECIALIST",
        "CLEANING",
        "SECURITY"
    ]:

        keyboard = executor_keyboard()



    else:

        keyboard = None



    await message.answer(

        f"""
👋 Добро пожаловать,
{employee['full_name']}


Ваша роль:

{role}
""",

        reply_markup=keyboard

    )
