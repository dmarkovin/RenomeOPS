from aiogram.types import ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

from app.services.employees.service import (
    get_employee,
    get_employee_by_invite,
    activate_employee,
)

from app.handlers.menu import show_main_menu


router = Router()


@router.message(CommandStart())
async def start_handler(
    message: Message
):

    print(
        "START RECEIVED:",
        message.from_user.id
    )


    employee = await get_employee(
        message.from_user.id
    )


    if employee:

        await show_main_menu(
            message
        )

        return



    args = message.text.split()


    if len(args) > 1:

        invite_code = args[1]


        employee = await get_employee_by_invite(
            invite_code
        )


        if employee is None:

            await message.answer(
                "❌ Приглашение не найдено."
            )

            return



        await activate_employee(
            employee.id,
            message.from_user.id,
            message.from_user.username
        )


        await message.answer(
            "✅ Вы зарегистрированы в системе."
        )


        await show_main_menu(
            message
        )

        return



    await message.answer(
        """
👋 Добро пожаловать в Renome OPS.

У вас пока нет доступа.

Получите приглашение от администратора.
"""
    )

    print(f"DEBUG: Received message: '{message.text}'")

async def become_admin(message: Message):
    from app.config import settings
    from app.database.models import UserRole
    from app.services.employees.service import get_employee, update_employee_role
    if str(message.from_user.id) != str(settings.ADMIN_TELEGRAM_ID):
        await message.answer("У вас нет прав.")
        return
    user = await get_employee(message.from_user.id)
    if not user:
        await message.answer("Вы не зарегистрированы.")
        return
    await update_employee_role(user.id, UserRole.ADMIN)
    await message.answer("✅ Ваша роль восстановлена до Администратора.")

async def cmd_profile(message: Message):
    from app.services.employees.service import get_employee
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    text = (
        f"👤 **Ваш профиль**\n\n"
        f"ФИО: {employee.full_name}\n"
        f"Телефон: {employee.phone or '—'}\n"
        f"Роль: {employee.role.value}\n"
        f"Команда: {employee.team.value if employee.team else '—'}\n"
        f"Активен: {'✅ Да' if employee.active else '❌ Нет'}\n"
        f"Telegram ID: {employee.telegram_id or '—'}\n"
        f"Дата регистрации: {employee.registered_at.strftime('%d.%m.%Y %H:%M') if employee.registered_at else '—'}"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(Command("become_admin"))
async def become_admin(message: Message):
    from app.config import settings
    from app.database.models import UserRole
    from app.services.employees.service import get_employee, update_employee_role
    if message.from_user.id not in settings.ADMIN_TELEGRAM_IDS:
        await message.answer("У вас нет прав.")
        return
    user = await get_employee(message.from_user.id)
    if not user:
        await message.answer("Вы не зарегистрированы.")
        return
    await update_employee_role(user.id, UserRole.ADMIN)
    await message.answer("✅ Ваша роль восстановлена до Администратора.")
