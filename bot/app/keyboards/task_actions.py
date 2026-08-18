from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import UserRole, User


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


def task_actions_keyboard(task, employee: User) -> InlineKeyboardMarkup:
    task_id = task.id
    status = task.status
    role = employee.role
    buttons = []

    # ====== Кнопка "Взять в работу" ======
    can_take = False
    if task.assigned_to is None and employee.team is not None:
        if task.assigned_team is None or task.assigned_team == employee.team:
            can_take = True
    if role in (UserRole.ADMIN, UserRole.CONCIERGE, UserRole.DIRECTOR):
        can_take = True

    if can_take and status not in ("closed", "checking"):
        buttons.append([InlineKeyboardButton(text="📥 Взять в работу", callback_data=f"task_take:{task_id}")])

    # ====== Если пользователь является исполнителем ======
    if task.assigned_to == employee.id:
        # Приостановить (если статус позволяет)
        if status in ("accepted", "in_progress"):
            buttons.append([InlineKeyboardButton(text="⏸ Приостановить", callback_data=f"task_pause:{task_id}")])
        # Возобновить (если статус paused)
        if status == "paused":
            buttons.append([InlineKeyboardButton(text="▶ Возобновить", callback_data=f"task_resume:{task_id}")])
        # Выполнено (на проверку) – для всех исполнителей, включая технику, клининг, охрану
        if status in ("in_progress", "paused", "accepted"):
            buttons.append([InlineKeyboardButton(text="✅ Выполнено", callback_data=f"task_check_start:{task_id}")])
        # Передать
        if status != "closed":
            buttons.append([InlineKeyboardButton(text="↗️ Передать", callback_data=f"task_transfer:{task_id}")])

    # ====== Для администратора, консьержа, директора ======
    if role in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE):
        if status != "closed":
            buttons.append([InlineKeyboardButton(text="👤 Назначить", callback_data=f"task_assign:{task_id}")])
        if status == "checking":
            buttons.append([
                InlineKeyboardButton(text="✅ Закрыть", callback_data=f"task_status:{task_id}:close"),
                InlineKeyboardButton(text="🔄 Вернуть на доработку", callback_data=f"task_status:{task_id}:rework"),
            ])
        if status != "closed" and role in (UserRole.ADMIN, UserRole.CONCIERGE):
            buttons.append([InlineKeyboardButton(text="🔒 Принудительно закрыть", callback_data=f"task_status:{task_id}:close")])
        if status == "waiting":
            buttons.append([InlineKeyboardButton(text="🔄 Вернуть в работу", callback_data=f"task_status:{task_id}:start")])

    # ====== Общие кнопки ======
    buttons.append([
        InlineKeyboardButton(text="💬 Комментарии", callback_data=f"task_comment_list:{task_id}"),
        InlineKeyboardButton(text="📷 Фото", callback_data=f"task_photo:{task_id}"),
    ])
    buttons.append([
        InlineKeyboardButton(text="📹 Видео", callback_data=f"task_video:{task_id}"),
        InlineKeyboardButton(text="📜 История", callback_data=f"task_history:{task_id}"),
    ])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="tasks_back")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
