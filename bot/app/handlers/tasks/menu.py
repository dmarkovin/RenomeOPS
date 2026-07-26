from aiogram import Router, F, types
from aiogram.types import Message

from app.services.employees.service import get_employee
from app.database.models import UserRole

router = Router()

@router.message(F.text == "📋 Заявки")
async def tasks_menu(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return

    # Формируем клавиатуру для подменю
    buttons = []
    # Список заявок (все открытые) – для ADMIN, DIRECTOR, CONCIERGE
    if employee.role in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE):
        buttons.append([types.KeyboardButton(text="📋 Список заявок")])
    # Мои заявки – для всех (исполнители и консьерж тоже могут иметь личные задачи)
    buttons.append([types.KeyboardButton(text="📋 Мои заявки")])
    # Архив – для всех
    buttons.append([types.KeyboardButton(text="📦 Архив")])
    # Создать заявку – для ADMIN, DIRECTOR, CONCIERGE
    if employee.role in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE):
        buttons.append([types.KeyboardButton(text="➕ Создать заявку")])
    # Назад
    buttons.append([types.KeyboardButton(text="⬅️ Назад")])

    keyboard = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await message.answer("📋 Управление заявками:", reply_markup=keyboard)
