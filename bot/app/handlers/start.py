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
