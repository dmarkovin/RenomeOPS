from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import UserRole, TaskStatus, User


def get_task_status_emoji(status: TaskStatus) -> str:
    emoji_map = {
        TaskStatus.CREATED: "🟡",
        TaskStatus.ACCEPTED: "🔵",
        TaskStatus.IN_PROGRESS: "🟠",
        TaskStatus.CHECKING: "🟣",
        TaskStatus.CLOSED: "✅",
    }
    return emoji_map.get(status, "⚪")


def task_actions_keyboard(task, employee: User) -> InlineKeyboardMarkup:
    task_id = task.id
    status = task.status
    role = employee.role
    buttons = []

    # ====== ADMIN, DIRECTOR, CONCIERGE ======
    if role in (UserRole.ADMIN, UserRole.CONCIERGE, UserRole.DIRECTOR):
        buttons.append([InlineKeyboardButton("👤 Назначить", callback_data=f"task_assign:{task_id}")])

        if status == TaskStatus.CHECKING:
            buttons.append([
                InlineKeyboardButton("✅ Закрыть", callback_data=f"task_status:{task_id}:close"),
                InlineKeyboardButton("🔄 Вернуть на доработку", callback_data=f"task_status:{task_id}:rework"),
            ])

        if status != TaskStatus.CLOSED and role in (UserRole.ADMIN, UserRole.CONCIERGE):
            buttons.append([InlineKeyboardButton("🔒 Принудительно закрыть", callback_data=f"task_status:{task_id}:close")])

    # ====== Исполнители (TECHNICIAN, CLEANER, SECURITY) ======
    if role in (UserRole.TECHNICIAN, UserRole.CLEANER, UserRole.SECURITY):
        # Задача назначена на команду и ещё не взята
        if task.assigned_team == employee.team and task.assigned_to is None:
            buttons.append([InlineKeyboardButton("📥 Взять в работу", callback_data=f"task_take:{task_id}")])
        # Если текущий пользователь является исполнителем (взял задачу)
        elif task.assigned_to == employee.id:
            if status == TaskStatus.CREATED or status == TaskStatus.ACCEPTED:
                buttons.append([InlineKeyboardButton("✅ Принять", callback_data=f"task_status:{task_id}:accept")])
            if status == TaskStatus.ACCEPTED:
                buttons.append([InlineKeyboardButton("▶ Начать выполнение", callback_data=f"task_status:{task_id}:start")])
            if status == TaskStatus.IN_PROGRESS:
                buttons.append([InlineKeyboardButton("🔄 На проверку", callback_data=f"task_status:{task_id}:check")])
            if status != TaskStatus.CLOSED:
                buttons.append([InlineKeyboardButton("↗️ Передать задачу", callback_data=f"task_transfer:{task_id}")])
        # Если задача уже взята другим членом команды – не показываем кнопку "Взять"
        # (можно добавить информационную кнопку, но пока пропускаем)

    # ====== Общие кнопки (комментарии, фото, история) ======
    buttons.append([
        InlineKeyboardButton("💬 Комментарий", callback_data=f"task_comment:{task_id}"),
        InlineKeyboardButton("📷 Фото", callback_data=f"task_photo:{task_id}"),
    ])
    buttons.append([
        InlineKeyboardButton("📜 История", callback_data=f"task_history:{task_id}"),
    ])
    buttons.append([InlineKeyboardButton("⬅️ Назад к списку", callback_data="tasks_back")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
