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

    # ====== Исполнители ======
    if role in (UserRole.TECHNICIAN, UserRole.CLEANER, UserRole.SECURITY):
        # Задача на команде (не взята) → только "Взять в работу"
        if task.assigned_team == employee.team and task.assigned_to is None:
            buttons.append([InlineKeyboardButton(text="📥 Взять в работу", callback_data=f"task_take:{task_id}")])
        # Если пользователь является исполнителем
        elif task.assigned_to == employee.id:
            # Кнопка "На проверку" – доступна всегда, если не закрыта и не на проверке
            if status not in (TaskStatus.CLOSED, TaskStatus.CHECKING):
                buttons.append([InlineKeyboardButton(text="🔄 На проверку", callback_data=f"task_status:{task_id}:check")])
            # Кнопка "Отложить" – только если в работе
            if status == TaskStatus.IN_PROGRESS:
                buttons.append([InlineKeyboardButton(text="⏰ Отложить", callback_data=f"task_wait:{task_id}")])
            if status == TaskStatus.WAITING:
                buttons.append([InlineKeyboardButton(text="▶ Вернуть в работу", callback_data=f"task_status:{task_id}:start")])
            # Передать – если не закрыта
            if status != TaskStatus.CLOSED:
                buttons.append([InlineKeyboardButton(text="↗️ Передать", callback_data=f"task_transfer:{task_id}")])

    # ====== Общие кнопки ======
    buttons.append([
        InlineKeyboardButton(text="💬 Комментарий", callback_data=f"task_comment:{task_id}"),
        InlineKeyboardButton(text="📷 Фото", callback_data=f"task_photo:{task_id}"),
    ])
    buttons.append([
        InlineKeyboardButton(text="📜 История", callback_data=f"task_history:{task_id}"),
    ])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="tasks_back")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
