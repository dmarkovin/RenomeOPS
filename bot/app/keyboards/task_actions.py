from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import UserRole, TaskStatus, User


def get_task_status_emoji(status: TaskStatus) -> str:
    emoji_map = {
        TaskStatus.CREATED: "🟡",
        TaskStatus.ACCEPTED: "🔵",
        TaskStatus.IN_PROGRESS: "🟠",
        TaskStatus.CHECKING: "🟣",
        TaskStatus.CLOSED: "✅",
        TaskStatus.WAITING: "⏳",
    }
    return emoji_map.get(status, "⚪")


def task_actions_keyboard(task, employee: User) -> InlineKeyboardMarkup:
    task_id = task.id
    status = task.status
    role = employee.role
    buttons = []

    # ====== Администратор, Директор, Консьерж ======
    if role in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE):
        if status != TaskStatus.CLOSED:
            buttons.append([InlineKeyboardButton(text="👤 Назначить", callback_data=f"task_assign:{task_id}")])

        if status == TaskStatus.CHECKING:
            buttons.append([
                InlineKeyboardButton(text="✅ Закрыть", callback_data=f"task_status:{task_id}:close"),
                InlineKeyboardButton(text="🔄 Вернуть на доработку", callback_data=f"task_status:{task_id}:rework"),
            ])

        if status != TaskStatus.CLOSED and role in (UserRole.ADMIN, UserRole.CONCIERGE):
            buttons.append([InlineKeyboardButton(text="🔒 Принудительно закрыть", callback_data=f"task_status:{task_id}:close")])

        if status == TaskStatus.WAITING:
            buttons.append([InlineKeyboardButton(text="🔄 Вернуть в работу", callback_data=f"task_status:{task_id}:start")])

    # ====== Исполнители (Техник, Клининг, Охрана) ======
    if role in (UserRole.TECHNICIAN, UserRole.CLEANER, UserRole.SECURITY):
        if task.assigned_team == employee.team and task.assigned_to is None:
            buttons.append([InlineKeyboardButton(text="📥 Взять в работу", callback_data=f"task_take:{task_id}")])
        elif task.assigned_to == employee.id:
            if status == TaskStatus.CREATED or status == TaskStatus.ACCEPTED:
                buttons.append([InlineKeyboardButton(text="✅ Принять", callback_data=f"task_status:{task_id}:accept")])
            if status == TaskStatus.ACCEPTED:
                buttons.append([InlineKeyboardButton(text="▶ Начать выполнение", callback_data=f"task_status:{task_id}:start")])
            if status == TaskStatus.IN_PROGRESS:
                buttons.append([InlineKeyboardButton(text="🔄 На проверку", callback_data=f"task_status:{task_id}:check")])
            if status != TaskStatus.CLOSED:
                buttons.append([InlineKeyboardButton(text="↗️ Передать", callback_data=f"task_transfer:{task_id}")])

    # ====== Добавление фото ======
    if role in (UserRole.ADMIN, UserRole.CONCIERGE) or (role in (UserRole.TECHNICIAN, UserRole.CLEANER, UserRole.SECURITY) and task.assigned_to == employee.id):
        buttons.append([InlineKeyboardButton(text="➕ Добавить фото", callback_data=f"task_add_photo:{task_id}")])

    # ====== Общие кнопки ======
    buttons.append([
        InlineKeyboardButton(text="💬 Комментарий", callback_data=f"task_comment_menu:{task_id}"),
        InlineKeyboardButton(text="📷 Фото", callback_data=f"task_photo:{task_id}"),
    ])
    buttons.append([
        InlineKeyboardButton(text="📜 История", callback_data=f"task_history:{task_id}"),
    ])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="tasks_back")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def comment_menu_keyboard(task_id: int) -> InlineKeyboardMarkup:
    """Клавиатура меню комментариев"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Посмотреть комментарии", callback_data=f"task_comment_list:{task_id}")],
        [InlineKeyboardButton(text="✏️ Добавить комментарий", callback_data=f"task_comment_add:{task_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"task_comment_back:{task_id}")],
    ])
