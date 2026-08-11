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

    # ====== Кнопка "Взять в работу" для исполнителей (только если нет исполнителя) ======
    can_take = False
    if task.assigned_to is None and employee.team is not None:
        # Для обычных исполнителей – только если задача назначена на их команду или без команды
        if task.assigned_team is None or task.assigned_team == employee.team:
            can_take = True
    # Администратор, консьерж, директор могут взять любую задачу (перехват)
    if role in (UserRole.ADMIN, UserRole.CONCIERGE, UserRole.DIRECTOR):
        can_take = True

    if can_take and status not in ("closed", "checking"):
        buttons.append([InlineKeyboardButton(text="📥 Взять в работу", callback_data=f"task_take:{task_id}")])

    # ====== Если пользователь является исполнителем (задача уже взята им) ======
    if task.assigned_to == employee.id:
        # Кнопка "Приостановить" – если задача в работе или принята
        if status in ("accepted", "in_progress"):
            buttons.append([InlineKeyboardButton(text="⏸ Приостановить", callback_data=f"task_pause:{task_id}")])
        # Кнопка "Возобновить" – если задача на паузе
        if status == "paused":
            buttons.append([InlineKeyboardButton(text="▶ Возобновить", callback_data=f"task_resume:{task_id}")])
        # Кнопка "Выполнено" – если задача в работе или на паузе
        if status in ("in_progress", "paused"):
            buttons.append([InlineKeyboardButton(text="✅ Выполнено", callback_data=f"task_status:{task_id}:check")])
        # Кнопка "Передать" – всегда для исполнителя
        if status != "closed":
            buttons.append([InlineKeyboardButton(text="↗️ Передать", callback_data=f"task_transfer:{task_id}")])

    # ====== Для администратора, консьержа, директора – дополнительные кнопки ======
    if role in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE):
        # Назначить – если задача не закрыта
        if status != "closed":
            buttons.append([InlineKeyboardButton(text="👤 Назначить", callback_data=f"task_assign:{task_id}")])
        # Проверка и закрытие
        if status == "checking":
            buttons.append([
                InlineKeyboardButton(text="✅ Закрыть", callback_data=f"task_status:{task_id}:close"),
                InlineKeyboardButton(text="🔄 Вернуть на доработку", callback_data=f"task_status:{task_id}:rework"),
            ])
        # Принудительное закрытие (для админа и консьержа)
        if status != "closed" and role in (UserRole.ADMIN, UserRole.CONCIERGE):
            buttons.append([InlineKeyboardButton(text="🔒 Принудительно закрыть", callback_data=f"task_status:{task_id}:close")])
        # Вернуть в работу из ожидания
        if status == "waiting":
            buttons.append([InlineKeyboardButton(text="🔄 Вернуть в работу", callback_data=f"task_status:{task_id}:start")])

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
