from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def role_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора роли"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👑 ADMIN")],
            [KeyboardButton(text="👨‍💼 DIRECTOR")],
            [KeyboardButton(text="🛎 CONCIERGE")],
            [KeyboardButton(text="🔧 TECHNICIAN")],
            [KeyboardButton(text="🧹 CLEANER")],
            [KeyboardButton(text="🛡 SECURITY")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
    )


def team_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора команды (для ролей, у которых есть команды)"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔧 TEAM_TECH")],
            [KeyboardButton(text="🧹 TEAM_CLEANING")],
            [KeyboardButton(text="🛡 TEAM_SECURITY")],
            [KeyboardButton(text="🏢 ADMINISTRATION")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
    )


def confirm_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура подтверждения создания"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да, создать")],
            [KeyboardButton(text="❌ Отмена")],
        ],
        resize_keyboard=True,
    )
