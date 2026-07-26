from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from app.services.employees.service import get_employee
from app.services.tasks.service import (
    get_open_tasks,
    get_tasks_for_employee,
    count_open_tasks,
    count_tasks_for_employee,
    get_tasks_by_status,
    count_tasks_by_status,
)
from app.database.models import UserRole, TaskStatus
from app.keyboards.tasks import task_list_keyboard, get_task_status_emoji

router = Router()

@router.message(F.text == "📋 Список заявок")
async def show_all_open_tasks(message: Message, page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return

    limit = 10
    offset = (page - 1) * limit
    tasks = await get_open_tasks(limit=limit, offset=offset)
    total = await count_open_tasks()
    total_pages = (total + limit - 1) // limit

    if not tasks:
        await message.answer("Нет открытых заявок.")
        return

    text = f"📋 Все открытые заявки (стр. {page}/{total_pages}):\n\n"
    for task in tasks:
        status_emoji = get_task_status_emoji(task.status)
        assignee_name = task.assignee.full_name if task.assignee else "не назначен"
        text += f"{status_emoji} #{task.id} **{task.title[:30]}**\n"
        text += f"   Приоритет: {task.priority} | Создал: {task.creator.full_name if task.creator else '—'}"
        text += f" | Исполнитель: {assignee_name}\n\n"

    await message.answer(
        text,
        reply_markup=task_list_keyboard(tasks, page, total_pages),
        parse_mode="HTML",
    )

@router.message(F.text == "📋 Мои заявки")
async def show_my_tasks(message: Message, page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return

    limit = 10
    offset = (page - 1) * limit
    tasks = await get_tasks_for_employee(employee.id, limit=limit, offset=offset)
    total = await count_tasks_for_employee(employee.id)
    total_pages = (total + limit - 1) // limit

    if not tasks:
        await message.answer("Нет задач для вас.")
        return

    text = f"📋 Мои заявки (стр. {page}/{total_pages}):\n\n"
    for task in tasks:
        status_emoji = get_task_status_emoji(task.status)
        assignee_name = task.assignee.full_name if task.assignee else "не назначен"
        text += f"{status_emoji} #{task.id} **{task.title[:30]}**\n"
        text += f"   Приоритет: {task.priority} | Создал: {task.creator.full_name if task.creator else '—'}"
        text += f" | Исполнитель: {assignee_name}\n\n"

    await message.answer(
        text,
        reply_markup=task_list_keyboard(tasks, page, total_pages),
        parse_mode="HTML",
    )

@router.message(F.text == "📦 Архив")
async def show_archive(message: Message, page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return

    limit = 10
    offset = (page - 1) * limit

    if employee.role in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE):
        tasks = await get_tasks_by_status(TaskStatus.CLOSED, limit=limit, offset=offset)
        total = await count_tasks_by_status(TaskStatus.CLOSED)
        title = "📦 Архив (все закрытые заявки)"
    else:
        tasks = await get_tasks_for_employee(employee.id, status=TaskStatus.CLOSED, limit=limit, offset=offset)
        total = await count_tasks_for_employee(employee.id, status=TaskStatus.CLOSED)
        title = "📦 Архив (мои закрытые заявки)"

    total_pages = (total + limit - 1) // limit

    if not tasks:
        await message.answer("Архив пуст.")
        return

    text = f"{title} (стр. {page}/{total_pages}):\n\n"
    for task in tasks:
        status_emoji = get_task_status_emoji(task.status)
        assignee_name = task.assignee.full_name if task.assignee else "не назначен"
        text += f"{status_emoji} #{task.id} **{task.title[:30]}**\n"
        text += f"   Приоритет: {task.priority} | Создал: {task.creator.full_name if task.creator else '—'}"
        text += f" | Исполнитель: {assignee_name}\n"
        if task.closed_at:
            text += f"   Закрыта: {task.closed_at.strftime('%d.%m.%Y %H:%M')}\n"
        text += "\n"

    await message.answer(
        text,
        reply_markup=task_list_keyboard(tasks, page, total_pages),
        parse_mode="HTML",
    )

@router.callback_query(F.data.startswith("task_page:"))
async def paginate_tasks(callback: CallbackQuery):
    await callback.answer("Пагинация в разработке")
    await callback.message.delete()
    await callback.message.answer("Нажмите кнопку 'Список заявок' или 'Мои заявки' для обновления.")

@router.callback_query(F.data == "tasks_back")
async def back_to_main(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()
