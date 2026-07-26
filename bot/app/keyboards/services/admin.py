from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def services_admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Новая услуга")],
            [KeyboardButton(text="📋 Список услуг")],
            [KeyboardButton(text="📊 Заказы")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )
