from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Заявки"),
                KeyboardButton(text="👥 Сотрудники"),
            ],
            [
                KeyboardButton(text="📊 Статистика"),
                KeyboardButton(text="⚙ Настройки"),
            ],
        ],
        resize_keyboard=True
    )
