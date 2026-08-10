from typing import Callable, Awaitable, Dict, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.employees.service import get_employee

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Определяем, является ли событие сообщением или callback-запросом
        is_message = isinstance(event, Message)
        is_callback = isinstance(event, CallbackQuery)

        # Пропускаем команды /start и /become_admin без проверки
        if is_message and event.text:
            if event.text.startswith(('/start', '/become_admin')):
                return await handler(event, data)

        # Получаем user_id
        user_id = None
        if is_message:
            user_id = event.from_user.id
        elif is_callback:
            user_id = event.from_user.id

        if user_id:
            session: AsyncSession = data.get('session')
            if session:
                employee = await get_employee(user_id)
                if not employee:
                    # Пользователь не зарегистрирован
                    if is_message:
                        await event.answer("❌ Вы не зарегистрированы. Используйте /start с приглашением.")
                    elif is_callback:
                        await event.answer("❌ Вы не зарегистрированы.", show_alert=True)
                    return  # не передаём управление дальше
                if not employee.active:
                    # Пользователь заблокирован
                    if is_message:
                        await event.answer("⛔ Ваш аккаунт заблокирован. Обратитесь к администратору.")
                    elif is_callback:
                        await event.answer("⛔ Ваш аккаунт заблокирован.", show_alert=True)
                    return  # не передаём управление дальше
        # Если всё ок, передаём управление дальше
        return await handler(event, data)
