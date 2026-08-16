from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from app.database.models import Task
from typing import List

def tasks_menu_keyboard(role: str) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="➕ Создать заявку")],
        [KeyboardButton(text="📋 Список заявок")],
        [KeyboardButton(text="📋 Мои задачи")],
        [KeyboardButton(text="📋 Новые задачи")],
    ]
    if role in ("ADMIN", "CONCIERGE", "DIRECTOR"):
        buttons.append([KeyboardButton(text="📋 Ожидают проверки")])
        buttons.append([KeyboardButton(text="📦 Архив")])
    if role in ("ADMIN", "DIRECTOR"):
        buttons.append([KeyboardButton(text="📊 Статистика")])
    buttons.append([KeyboardButton(text="🔍 Поиск по заявкам")])
    buttons.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def task_list_keyboard(
    tasks: List[Task],
    page: int,
    total_pages: int,
    list_type: str = "open",
    filter_priority: int = None
) -> InlineKeyboardMarkup:
    buttons = []
    for task in tasks[:10]:
        priority = int(task.priority) if task.priority is not None else 3
        status_emoji = get_task_status_emoji(task.status)
        priority_emoji = get_priority_emoji(priority)
        text = f"{status_emoji} {priority_emoji} #{task.id} {task.title[:25]}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"task:{task.id}")])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"task_page:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Вперед ▶️", callback_data=f"task_page:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    sort_buttons = []
    sort_buttons.append(InlineKeyboardButton("📅 По дате", callback_data="task_sort:date"))
    sort_buttons.append(InlineKeyboardButton("🔥 По приоритету", callback_data="task_sort:priority"))
    buttons.append(sort_buttons)

    buttons.append([InlineKeyboardButton("⬅️ В главное меню", callback_data="tasks_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_task_status_emoji(status: str) -> str:
    emoji_map = {
        "created": "🟡",
        "accepted": "🔵",
        "in_progress": "🟠",
        "checking": "🟣",
        "closed": "✅",
        "waiting": "⏰",
        "paused": "⏸️",
    }
    return emoji_map.get(status, "⚪")

def get_priority_emoji(priority: int) -> str:
    if not isinstance(priority, int):
        try:
            priority = int(priority)
        except (ValueError, TypeError):
            priority = 3
    if priority <= 1:
        return "🟢"
    elif priority <= 3:
        return "🟡"
    else:
        return "🔴"

def get_priority_name(priority: int) -> str:
    if not isinstance(priority, int):
        try:
            priority = int(priority)
        except (ValueError, TypeError):
            priority = 3
    return {1: "Низкий", 2: "Средний", 3: "Высокий", 4: "Критичный", 5: "Аварийный"}.get(priority, str(priority))
