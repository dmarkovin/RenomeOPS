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

def get_priority_emoji(priority: int) -> str:
    if priority <= 1:
        return "🟢"
    elif priority <= 3:
        return "🟡"
    else:
        return "🔴"

def get_priority_name(priority: int) -> str:
    return {1: "Низкий", 2: "Средний", 3: "Высокий", 4: "Критичный", 5: "Аварийный"}.get(priority, str(priority))

def task_list_keyboard(tasks: List, page: int, total_pages: int, list_type: str = "open", filter_priority: int = None) -> InlineKeyboardMarkup:
    buttons = []
    for task in tasks[:10]:
        status_emoji = get_task_status_emoji(task.status)
        priority_emoji = get_priority_emoji(task.priority)
        text = f"{status_emoji} {priority_emoji} #{task.id} {task.title[:25]}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"task:{task.id}")])

    # Навигация
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"task_page:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Вперед ▶️", callback_data=f"task_page:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    # Кнопки сортировки и фильтра
    sort_buttons = []
    sort_buttons.append(InlineKeyboardButton("📅 По дате", callback_data="task_sort:date"))
    sort_buttons.append(InlineKeyboardButton("🔥 По приоритету", callback_data="task_sort:priority"))
    buttons.append(sort_buttons)

    filter_buttons = []
    filter_buttons.append(InlineKeyboardButton("🔽 Все", callback_data="task_filter:all"))
    for p in [1, 2, 3, 4, 5]:
        label = f"{p}★"
        if filter_priority == p:
            label = f"✅ {p}★"
        filter_buttons.append(InlineKeyboardButton(label, callback_data=f"task_filter:{p}"))
    buttons.append(filter_buttons)

    buttons.append([InlineKeyboardButton("⬅️ В главное меню", callback_data="tasks_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
