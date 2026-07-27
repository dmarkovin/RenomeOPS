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

    # ====== Администратор, Директор, Консьерж ======
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

    # ====== ВСЕ СОТРУДНИКИ (кроме ADMIN? оставим для всех) ======
    # Кнопка "Взять в работу" доступна всем, у кого есть команда,
    # если задача назначена на его команду и не взята (assigned_to is None)
    if task.assigned_team == employee.team and task.assigned_to is None and employee.team is not None:
        buttons.append([InlineKeyboardButton(text="📥 Взять в работу", callback_data=f"task_take:{task_id}")])

    # Если пользователь является исполнителем (задача уже взята им)
    if task.assigned_to == employee.id:
        if status == "created" or status == "accepted":
            buttons.append([InlineKeyboardButton(text="✅ Принять", callback_data=f"task_status:{task_id}:accept")])
        if status == "accepted":
            buttons.append([InlineKeyboardButton(text="▶ Начать выполнение", callback_data=f"task_status:{task_id}:start")])
        if status == "in_progress":
            if status == "in_progress":
                buttons.append([InlineKeyboardButton(text="⏸ Приостановить", callback_data=f"task_status:{task_id}:pause")])
            if status == "paused":
                buttons.append([InlineKeyboardButton(text="▶ Возобновить", callback_data=f"task_status:{task_id}:resume")])
            buttons.append([InlineKeyboardButton(text="🔄 На проверку", callback_data=f"task_status:{task_id}:check")])
        if status != "closed":
            buttons.append([InlineKeyboardButton(text="↗️ Передать", callback_data=f"task_transfer:{task_id}")])

    # ====== Добавление фото ======
    if role in (UserRole.ADMIN, UserRole.CONCIERGE) or (role in (UserRole.TECHNICIAN, UserRole.CLEANER, UserRole.SECURITY) and task.assigned_to == employee.id):
        buttons.append([InlineKeyboardButton(text="➕ Добавить фото", callback_data=f"task_add_photo:{task_id}")])

    # ====== Общие кнопки ======
    buttons.append([
        InlineKeyboardButton(text="💬 Комментарии", callback_data=f"task_comment_menu:{task_id}"),
        InlineKeyboardButton(text="📷 Фото", callback_data=f"task_photo:{task_id}"),
    ])
    buttons.append([
        InlineKeyboardButton(text="📜 История", callback_data=f"task_history:{task_id}"),
    ])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="tasks_back")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
