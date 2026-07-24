from aiogram import Router
from aiogram.types import Message

from app.services.employee_service import get_employee

from app.utils.roles import (
    SUPER_ADMIN,
    DIRECTOR,
    CONCIERGE,
    TECHNICIAN,
    CLEANING,
    SECURITY,
)

from app.keyboards.admin import admin_keyboard
from app.keyboards.director import director_keyboard
from app.keyboards.concierge import concierge_keyboard
from app.keyboards.technician import technician_keyboard
from app.keyboards.cleaning import cleaning_keyboard
from app.keyboards.security import security_keyboard


router = Router()


async def show_main_menu(message: Message):

    employee = await get_employee(message.from_user.id)

    if not employee:

        await message.answer(
            "Вы не зарегистрированы в системе."
        )
        return

    role = employee["role"]

    if role == SUPER_ADMIN:

        await message.answer(
            "👑 Главное меню",
            reply_markup=admin_keyboard()
        )

    elif role == DIRECTOR:

        await message.answer(
            "👨‍💼 Главное меню",
            reply_markup=director_keyboard()
        )

    elif role == CONCIERGE:

        await message.answer(
            "🛎 Главное меню",
            reply_markup=concierge_keyboard()
        )

    elif role == TECHNICIAN:

        await message.answer(
            "🔧 Главное меню",
            reply_markup=technician_keyboard()
        )

    elif role == CLEANING:

        await message.answer(
            "🧹 Главное меню",
            reply_markup=cleaning_keyboard()
        )

    elif role == SECURITY:

        await message.answer(
            "🛡 Главное меню",
            reply_markup=security_keyboard()
        )

    else:

        await message.answer(
            "Роль не определена."
        )
