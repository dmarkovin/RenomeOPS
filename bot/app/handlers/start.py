from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command


router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):

    await message.answer(
        """
👋 Добро пожаловать в Renome OPS

Система управления исполнителями.

Доступные команды:

/start - запуск
/help - помощь
/profile - профиль
"""
    )
