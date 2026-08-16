from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from app.database.models import UserRole
from .admin import admin_keyboard
from .director import director_keyboard
from .concierge import concierge_keyboard
from .technician import technician_keyboard
from .cleaning import cleaning_keyboard
from .security import security_keyboard

def main_menu_keyboard(role: UserRole) -> ReplyKeyboardMarkup:
    if role == UserRole.ADMIN:
        return admin_keyboard()
    elif role == UserRole.DIRECTOR:
        return director_keyboard()
    elif role == UserRole.CONCIERGE:
        return concierge_keyboard()
    elif role == UserRole.TECHNICIAN:
        return technician_keyboard()
    elif role == UserRole.CLEANER:
        return cleaning_keyboard()
    elif role == UserRole.SECURITY:
        return security_keyboard()
    else:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📋 Меню")]],
            resize_keyboard=True
        )
