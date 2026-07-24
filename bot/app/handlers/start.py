from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from app.services.employee_service import (
    get_employee,
    get_employee_by_invite,
    activate_employee,
)

from app.handlers.menu import show_main_menu


router = Router()


@router.message(Command("start"))
async def start_handler(
    message: Message,
    command: CommandObject,
):

    telegram_id = message.from_user.id
    username = message.from_user.username

    employee = await get_employee(telegram_id)

    if employee:

        await show_main_menu(message)
        return

    if command.args:

        invite_code = command.args.strip()

        invited = await get_employee_by_invite(invite_code)

        if invited:

            await activate_employee(
                invited["id"],
                telegram_id,
                username,
            )

            await message.answer(
                f"""
✅ Регистрация завершена!

Добро пожаловать,
{invited['full_name']}
"""
            )

            await show_main_menu(message)
            return

    await message.answer(
        """
👋 Добро пожаловать в Renome OPS.

У вас пока нет доступа.

Используйте приглашение,
полученное от администратора.
"""
    )
