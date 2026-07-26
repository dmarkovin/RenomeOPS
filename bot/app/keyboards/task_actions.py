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
    """
    Генерирует инлайн‑клавиатуру для карточки заявки в зависимости от:
    - роли пользователя (employee)
    - статуса задачи
    - является ли пользователь исполнителем или членом команды
    """
    task_id = task.id
    status = task.status
    role = employee.role
    buttons = []

    # ====== Администратор, Директор, Консьерж ======
    if role in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE):
        # Кнопка назначения (если не закрыта)
        if status != TaskStatus.CLOSED:
            buttons.append([InlineKeyboardButton(text="👤 Назначить", callback_data=f"task_assign:{task_id}")])

        # Если задача на проверке (CHECKING) – кнопки закрыть/вернуть на доработку
        if status == TaskStatus.CHECKING:
            buttons.append([
                InlineKeyboardButton(text="✅ Закрыть", callback_data=f"task_status:{task_id}:close"),
                InlineKeyboardButton(text="🔄 Вернуть на доработку", callback_data=f"task_status:{task_id}:rework"),
            ])

        # Принудительное закрытие (если не закрыта)
        if status != TaskStatus.CLOSED and role in (UserRole.ADMIN, UserRole.CONCIERGE):
            buttons.append([InlineKeyboardButton(text="🔒 Принудительно закрыть", callback_data=f"task_status:{task_id}:close")])

    # ====== Исполнители (Техник, Клининг, Охрана) ======
    if role in (UserRole.TECHNICIAN, UserRole.CLEANER, UserRole.SECURITY):
        # Задача назначена на команду и не взята → кнопка "Взять в работу"
        if task.assigned_team == employee.team and task.assigned_to is None:
            buttons.append([InlineKeyboardButton(text="📥 Взять в работу", callback_data=f"task_take:{task_id}")])
        # Если пользователь является исполнителем
        elif task.assigned_to == employee.id:
            # Кнопки изменения статуса
            if status == TaskStatus.CREATED or status == TaskStatus.ACCEPTED:
                buttons.append([InlineKeyboardButton(text="✅ Принять", callback_data=f"task_status:{task_id}:accept")])
            if status == TaskStatus.ACCEPTED:
                buttons.append([InlineKeyboardButton(text="▶ Начать выполнение", callback_data=f"task_status:{task_id}:start")])
            if status == TaskStatus.IN_PROGRESS:
                buttons.append([InlineKeyboardButton(text="🔄 На проверку", callback_data=f"task_status:{task_id}:check")])
            if status != TaskStatus.CLOSED:
                buttons.append([InlineKeyboardButton(text="↗️ Передать задачу", callback_data=f"task_transfer:{task_id}")])
        # Если задача уже взята другим членом команды – ничего не показываем (или можно информационную кнопку)

    # ====== Общие кнопки (комментарии, фото, история) ======
    # Эти кнопки доступны всем, у кого есть доступ к карточке
    buttons.append([
        InlineKeyboardButton(text="💬 Комментарий", callback_data=f"task_comment:{task_id}"),
        InlineKeyboardButton(text="📷 Фото", callback_data=f"task_photo:{task_id}"),
    ])
    buttons.append([
        InlineKeyboardButton(text="📜 История", callback_data=f"task_history:{task_id}"),
    ])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="tasks_back")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
