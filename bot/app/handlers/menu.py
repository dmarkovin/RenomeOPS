from aiogram import Router
from aiogram.types import Message

from app.services.employees.service import get_employee
from app.database.models import UserRole

from app.keyboards.admin import admin_keyboard
from app.keyboards.director import director_keyboard
from app.keyboards.concierge import concierge_keyboard
from app.keyboards.technician import technician_keyboard
from app.keyboards.cleaning import cleaning_keyboard
from app.keyboards.security import security_keyboard


router = Router()



async def show_main_menu(
    message: Message
):

    employee = await get_employee(
        message.from_user.id
    )


    if employee is None:

        await message.answer(
            "Вы не зарегистрированы в системе."
        )

        return



    if employee.role == UserRole.ADMIN:

        await message.answer(
            "👑 Главное меню",
            reply_markup=admin_keyboard()
        )


    elif employee.role == UserRole.DIRECTOR:

        await message.answer(
            "👨‍💼 Главное меню",
            reply_markup=director_keyboard()
        )


    elif employee.role == UserRole.CONCIERGE:

        await message.answer(
            "🛎 Главное меню",
            reply_markup=concierge_keyboard()
        )


    elif employee.role == UserRole.TECHNICIAN:

        await message.answer(
            "🔧 Главное меню",
            reply_markup=technician_keyboard()
        )


    elif employee.role == UserRole.CLEANER:

        await message.answer(
            "🧹 Главное меню",
            reply_markup=cleaning_keyboard()
        )


    elif employee.role == UserRole.SECURITY:

        await message.answer(
            "🛡 Главное меню",
            reply_markup=security_keyboard()
        )


    else:

        await message.answer(
            f"Неизвестная роль: {employee.role}"
        )
