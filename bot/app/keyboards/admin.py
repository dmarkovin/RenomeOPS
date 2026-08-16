from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👥 Сотрудники"),
                KeyboardButton(text="💳 Управление услугами"),
            ],
            [
                KeyboardButton(text="📋 Заявки"),
                KeyboardButton(text="📊 Статистика"),
            ],
            [
                KeyboardButton(text="🚗 Пропуска"),
                KeyboardButton(text="📦 Доставка"),
            ],
            [
                KeyboardButton(text="⚙️ Настройки"),
            ],
        ],
        resize_keyboard=True
    )
