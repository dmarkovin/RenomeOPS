from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command


from app.services.employee_service import get_employee


from app.keyboards.admin import admin_keyboard
from app.keyboards.director import director_keyboard
from app.keyboards.concierge import concierge_keyboard
from app.keyboards.technical import technical_keyboard
from app.keyboards.cleaning import cleaning_keyboard
from app.keyboards.security import security_keyboard



router = Router()



@router.message(Command("start"))
@router.message(Command("menu"))
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



    keyboard = None



    if role == "SUPER_ADMIN":

        keyboard = admin_keyboard()



    elif role == "DIRECTOR":

        keyboard = director_keyboard()



    elif role == "CONCIERGE":

        keyboard = concierge_keyboard()



    elif role == "TECH_SPECIALIST":

        keyboard = technical_keyboard()



    elif role == "CLEANING":

        keyboard = cleaning_keyboard()



    elif role == "SECURITY":

        keyboard = security_keyboard()



    await message.answer(

        f"""
👋 Добро пожаловать,
{employee['full_name']}


🏢 Renome OPS


Ваша роль:

{role}
""",

        reply_markup=keyboard

    )
