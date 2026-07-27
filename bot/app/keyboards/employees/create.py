from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def role_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👑 ADMIN")],
            [KeyboardButton(text="👨‍💼 DIRECTOR")],
            [KeyboardButton(text="🛎 CONCIERGE")],
            [KeyboardButton(text="🔧 TECHNICIAN")],
            [KeyboardButton(text="🧹 CLEANER")],
            [KeyboardButton(text="🛡 SECURITY")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True
    )

def confirm_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да, создать")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True
    )
