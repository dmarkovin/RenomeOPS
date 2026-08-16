from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.database.models import UserRole

def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Сотрудники"), KeyboardButton(text="💳 Управление услугами")],
            [KeyboardButton(text="📋 Заявки"), KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="Пропуска"), KeyboardButton(text="Доставка")],
            [KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True
    )

def director_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Заявки"), KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="Пропуска"), KeyboardButton(text="Доставка")],
            [KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True
    )

def concierge_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Заявки"), KeyboardButton(text="Пропуска")],
            [KeyboardButton(text="Доставка"), KeyboardButton(text="📄 Документы")],
            [KeyboardButton(text="🔑 Ключи"), KeyboardButton(text="💳 Платные услуги")],
            [KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True
    )

def technician_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Заявки")],
            [KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True
    )

def cleaner_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Заявки")],
            [KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True
    )

def security_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Заявки"), KeyboardButton(text="Пропуска")],
            [KeyboardButton(text="🚶 Обходы")],
            [KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True
    )

def main_menu_keyboard(role: UserRole) -> ReplyKeyboardMarkup:
    if role == UserRole.ADMIN:
        return admin_keyboard()
    elif role == UserRole.DIRECTOR:
        return director_keyboard()
    elif role == UserRole.CONCIERGE:
        return concierge_keyboard()
    elif role == UserRole.TECHNICIAN:
        return technician_keyboard()
    elif role == UserRole.CLEANER:
        return cleaner_keyboard()
    elif role == UserRole.SECURITY:
        return security_keyboard()
    else:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📋 Меню")]],
            resize_keyboard=True
        )
