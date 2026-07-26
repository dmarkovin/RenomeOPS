from aiogram.types import ReplyKeyboardMarkup
from aiogram.types import KeyboardButton


def concierge_menu():

    return ReplyKeyboardMarkup(

        keyboard=[

            [

                KeyboardButton(text="📋 Заявки"),

                KeyboardButton(text="💳 Платные услуги"),

            ],

            [

                KeyboardButton(text="🚗 Пропуска"),

                KeyboardButton(text="🔄 Обходы"),

            ],

            [

                KeyboardButton(text="📦 Посылки"),

                KeyboardButton(text="🗝 Ключи"),

            ],

            [

                KeyboardButton(text="📑 Документы"),

                KeyboardButton(text="📊 Отчеты"),

            ],

            [

                KeyboardButton(text="⚙ Настройки"),

            ],

        ],

        resize_keyboard=True,

    )


def technician_menu():

    return ReplyKeyboardMarkup(

        keyboard=[

            [

                KeyboardButton(text="📋 Новые заявки"),

            ],

            [

                KeyboardButton(text="🚧 Мои заявки"),

            ],

            [

                KeyboardButton(text="📦 Архив"),

            ],

            [

                KeyboardButton(text="👤 Профиль"),

            ],

        ],

        resize_keyboard=True,

    )


def director_menu():

    return ReplyKeyboardMarkup(

        keyboard=[

            [

                KeyboardButton(text="📊 Статистика"),

            ],

            [

                KeyboardButton(text="📋 Все заявки"),

            ],

            [

                KeyboardButton(text="👥 Сотрудники"),

            ],

            [

                KeyboardButton(text="📈 Отчеты"),

            ],

            [

                KeyboardButton(text="⚙ Настройки"),

            ],

        ],

        resize_keyboard=True,

    )
