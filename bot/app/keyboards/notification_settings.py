from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import UserSettings

def get_status_emoji(value: bool) -> str:
    return "✅" if value else "❌"

def notification_settings_keyboard(settings: UserSettings) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"{get_status_emoji(settings.notify_task_assigned)} Назначение задачи",
            callback_data="notif_toggle:notify_task_assigned"
        )],
        [InlineKeyboardButton(
            text=f"{get_status_emoji(settings.notify_task_mentioned)} Упоминания в комментариях",
            callback_data="notif_toggle:notify_task_mentioned"
        )],
        [InlineKeyboardButton(
            text=f"{get_status_emoji(settings.notify_task_status_changed)} Изменение статуса",
            callback_data="notif_toggle:notify_task_status_changed"
        )],
        [InlineKeyboardButton(
            text=f"{get_status_emoji(settings.notify_task_comment)} Новые комментарии",
            callback_data="notif_toggle:notify_task_comment"
        )],
        [InlineKeyboardButton(
            text=f"{get_status_emoji(settings.notify_task_closed)} Закрытие задачи",
            callback_data="notif_toggle:notify_task_closed"
        )],
        [InlineKeyboardButton(
            text=f"{get_status_emoji(settings.notify_new_task_team)} Новая задача на команду",
            callback_data="notif_toggle:notify_new_task_team"
        )],
        [InlineKeyboardButton(
            text=f"{get_status_emoji(settings.notify_checking)} Задача на проверке",
            callback_data="notif_toggle:notify_checking"
        )],
        [InlineKeyboardButton(
            text=f"{get_status_emoji(settings.notify_admin)} Общие уведомления (админ)",
            callback_data="notif_toggle:notify_admin"
        )],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="notif_back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
