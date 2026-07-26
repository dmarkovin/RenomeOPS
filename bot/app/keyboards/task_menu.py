from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def task_menu_management() -> ReplyKeyboardMarkup:
    """Подменю для управления заявками (ADMIN, DIRECTOR, CONCIERGE)"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Создать заявку")],
            [KeyboardButton(text="📋 Список открытых")],
            [KeyboardButton(text="📦 Архив")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )

def task_menu_executor() -> ReplyKeyboardMarkup:
    """Подменю для исполнителей (TECHNICIAN, CLEANER, SECURITY)"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Мои заявки")],
            [KeyboardButton(text="📦 Архив")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )
