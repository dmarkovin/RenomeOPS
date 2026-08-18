from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from app.database.models import TaskStatus, UserRole
from typing import List

def get_priority_emoji(priority):
    try:
        priority = int(priority)
    except (ValueError, TypeError):
        return "⚪"
    if priority >= 5: return "🔴"
    elif priority >= 4: return "🟠"
    elif priority >= 3: return "🟡"
    elif priority >= 2: return "🟢"
    else: return "⚪"

def get_priority_name(priority) -> str:
    try:
        priority = int(priority)
    except (ValueError, TypeError):
        return "Не указан"
    mapping = {
        5: "Критический",
        4: "Высокий",
        3: "Средний",
        2: "Низкий",
        1: "Неважно",
    }
    return mapping.get(priority, f"Приоритет {priority}")

def get_task_status_emoji(status: str) -> str:
    emoji_map = {
        "created": "📌",
        "accepted": "📋",
        "in_progress": "⚙️",
        "checking": "🔍",
        "closed": "✅",
        "waiting": "⏰",
        "paused": "⏸️",
    }
    return emoji_map.get(status, "⚪")

def get_assignment_emoji(task) -> str:
    if task.assigned_to is not None:
        return "👤"
    elif task.assigned_team is not None:
        return "👥"
    else:
        return "❓"

def task_list_keyboard(tasks: List, page: int, total_pages: int, list_type: str = "open", current_filter: int = None) -> InlineKeyboardMarkup:
    buttons = []
    for task in tasks[:10]:
        status_emoji = get_task_status_emoji(task.status)
        priority_emoji = get_priority_emoji(task.priority)
        paid_marker = "💰 " if getattr(task, 'is_paid', False) else ""
        assign_emoji = get_assignment_emoji(task)
        text = f"{status_emoji} {priority_emoji} {assign_emoji} #{task.id} {paid_marker}{task.title[:25]}"
        if list_type == "team" and task.assigned_to is None:
            buttons.append([
                InlineKeyboardButton(text=text, callback_data=f"task:{task.id}"),
                InlineKeyboardButton(text="📥 Взять", callback_data=f"task_take_from_list:{task.id}"),
            ])
        else:
            buttons.append([InlineKeyboardButton(text=text, callback_data=f"task:{task.id}")])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"task_page:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"task_page:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    buttons.append([
        InlineKeyboardButton(text="📅 По дате", callback_data="task_sort:date"),
        InlineKeyboardButton(text="🔥 По приоритету", callback_data="task_sort:priority"),
    ])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="tasks_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def tasks_menu_keyboard(role: UserRole) -> ReplyKeyboardMarkup:
    if role == UserRole.ADMIN:
        buttons = [
            [KeyboardButton(text="➕ Создать заявку")],
            [KeyboardButton(text="📋 Список заявок")],
            [KeyboardButton(text="📋 Мои задачи")],
            [KeyboardButton(text="🔍 Поиск по заявкам")],
            [KeyboardButton(text="📦 Архив")],
            [KeyboardButton(text="⚙ Настройки")],
            [KeyboardButton(text="⬅️ Назад")]
        ]
    elif role == UserRole.DIRECTOR:
        buttons = [
            [KeyboardButton(text="➕ Создать заявку")],
            [KeyboardButton(text="📋 Список заявок")],
            [KeyboardButton(text="🔍 Поиск по заявкам")],
            [KeyboardButton(text="📦 Архив")],
            [KeyboardButton(text="⚙ Настройки")],
            [KeyboardButton(text="⬅️ Назад")]
        ]
    elif role == UserRole.CONCIERGE:
        buttons = [
            [KeyboardButton(text="➕ Создать заявку")],
            [KeyboardButton(text="📋 Список заявок")],
            [KeyboardButton(text="📋 Мои задачи")],
            [KeyboardButton(text="📋 Ожидают проверки")],
            [KeyboardButton(text="🔍 Поиск по заявкам")],
            [KeyboardButton(text="📦 Архив")],
            [KeyboardButton(text="⚙ Настройки")],
            [KeyboardButton(text="⬅️ Назад")]
        ]
    else:
        buttons = [
            [KeyboardButton(text="📋 Мои задачи")],
            [KeyboardButton(text="📋 Новые задачи")],
            [KeyboardButton(text="📦 Архив")],
            [KeyboardButton(text="⚙ Настройки")],
            [KeyboardButton(text="⬅️ Назад")]
        ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
