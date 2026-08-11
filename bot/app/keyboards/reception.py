from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def reception_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Новая посылка")],
            [KeyboardButton(text="📋 Список посылок")],
            [KeyboardButton(text="📦 Архив доставки")],
            [KeyboardButton(text="🔑 Ключи")],
            [KeyboardButton(text="📄 Документы")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )
