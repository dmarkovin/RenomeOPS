from aiogram.types import ReplyKeyboardMarkup, KeyboardButton



def admin_menu():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="👥 Сотрудники"
                ),
                KeyboardButton(
                    text="📋 Задачи"
                )
            ],
            [
                KeyboardButton(
                    text="📊 Отчеты"
                ),
                KeyboardButton(
                    text="⚙️ Настройки"
                )
            ]
        ],
        resize_keyboard=True
    )



def concierge_menu():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="➕ Новая заявка"
                )
            ],
            [
                KeyboardButton(
                    text="📋 Мои заявки"
                )
            ],
            [
                KeyboardButton(
                    text="👷 Исполнители"
                )
            ]
        ],
        resize_keyboard=True
    )



def director_menu():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📊 Отчеты"
                )
            ],
            [
                KeyboardButton(
                    text="👥 Сотрудники"
                )
            ],
            [
                KeyboardButton(
                    text="📋 Задачи"
                )
            ]
        ],
        resize_keyboard=True
    )



def executor_menu():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📋 Мои задачи"
                )
            ],
            [
                KeyboardButton(
                    text="✅ Выполненные"
                )
            ],
            [
                KeyboardButton(
                    text="👤 Профиль"
                )
            ]
        ],
        resize_keyboard=True
    )
