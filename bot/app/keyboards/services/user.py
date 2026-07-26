from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def services_user_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Услуги")],
            [KeyboardButton(text="📦 Мои заказы")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )
