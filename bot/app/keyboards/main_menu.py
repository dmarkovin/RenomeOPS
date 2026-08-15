from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.database.models import UserRole

def main_menu_keyboard(role: UserRole) -> ReplyKeyboardMarkup:
    buttons = []

    if role == UserRole.ADMIN:
        buttons = [
            [KeyboardButton(text="👥 Сотрудники"), KeyboardButton(text="💳 Управление услугами")],
            [KeyboardButton(text="📋 Заявки"), KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="🚗 Пропуска")],
            [KeyboardButton(text="⚙ Настройки")],
        ]
    elif role == UserRole.DIRECTOR:
        buttons = [
            [KeyboardButton(text="📋 Заявки"), KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="🚗 Пропуска")],
            [KeyboardButton(text="⚙ Настройки")],
        ]
    elif role == UserRole.CONCIERGE:
        buttons = [
            [KeyboardButton(text="📋 Заявки")],
            [KeyboardButton(text="📦 Доставка")],
            [KeyboardButton(text="🔑 Ключи")],
            [KeyboardButton(text="📄 Документы")],
            [KeyboardButton(text="🚗 Пропуска")],
            [KeyboardButton(text="⚙ Настройки")],
        ]
    elif role == UserRole.SECURITY:
        buttons = [
            [KeyboardButton(text="📋 Заявки")],
            [KeyboardButton(text="🚗 Пропуска")],
            [KeyboardButton(text="🚶 Обходы")],
            [KeyboardButton(text="⚙ Настройки")],
        ]
    else:
        # TECHNICIAN, CLEANER и др.
        buttons = [
            [KeyboardButton(text="📋 Заявки")],
            [KeyboardButton(text="⚙ Настройки")],
        ]

    # Добавляем общую кнопку "Сообщить о проблеме" для всех
    buttons.append([KeyboardButton(text="📢 Сообщить о проблеме")])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
