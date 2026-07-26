from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import TaskStatus
from typing import List

def get_task_status_emoji(status: TaskStatus) -> str:
    emoji_map = {
        TaskStatus.CREATED: "🟡",
        TaskStatus.ACCEPTED: "🔵",
        TaskStatus.IN_PROGRESS: "🟠",
        TaskStatus.CHECKING: "🟣",
        TaskStatus.CLOSED: "✅",
    }
    return emoji_map.get(status, "⚪")

def task_list_keyboard(tasks: List, page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons = []
    for task in tasks[:10]:
        status_emoji = get_task_status_emoji(task.status)
        text = f"{status_emoji} #{task.id} {task.title[:25]}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"task:{task.id}")])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"task_page:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Вперед ▶️", callback_data=f"task_page:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    buttons.append([InlineKeyboardButton("⬅️ В главное меню", callback_data="tasks_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
