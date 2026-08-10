from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def reception_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Посылка")],
            [KeyboardButton(text="📄 Документы")],
            [KeyboardButton(text="📦 Архив доставки")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )
