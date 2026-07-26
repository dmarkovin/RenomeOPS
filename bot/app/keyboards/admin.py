from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Заявки"),
                KeyboardButton(text="💳 Платные услуги"),
            ],
            [
                KeyboardButton(text="👥 Сотрудники"),
                KeyboardButton(text="🚗 Пропуска"),
            ],
            [
                KeyboardButton(text="➕ Создать услугу"),
                KeyboardButton(text="📊 Статистика"),
            ],
            [
                KeyboardButton(text="⚙ Настройки"),
            ],
        ],
        resize_keyboard=True
    )
