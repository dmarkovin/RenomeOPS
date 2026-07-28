from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def reception_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Посылка")],
            [KeyboardButton(text="📄 Документ")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )

def delivery_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Новая посылка")],
            [KeyboardButton(text="📋 Активные посылки")],
            [KeyboardButton(text="📦 Архив посылок")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )

def document_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Новый документ")],
            [KeyboardButton(text="📋 Активные документы")],
            [KeyboardButton(text="📦 Архив документов")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )
