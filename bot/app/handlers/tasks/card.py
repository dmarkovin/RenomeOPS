from aiogram import Router, F, types
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter
from datetime import datetime, timedelta

from app.services.tasks.service import (
    get_task,
    change_status,
    add_comment,
    add_photo,
    get_task_history,
    take_task,
)
from app.services.employees.service import get_employee
from app.database.models import UserRole
from app.keyboards.task_actions import task_actions_keyboard, get_task_status_emoji
from app.keyboards.waiting import waiting_time_keyboard
from app.services.notification_service import notify_user, notify_admins, notify_concierges
from app.states.tasks.waiting import TaskWaiting
from app.states.tasks.photo import TaskAddPhoto
from app.handlers.tasks.list import show_list

router = Router()

class TaskCommentState(StatesGroup):
    waiting_for_comment = State()

class TaskPhotoState(StatesGroup):
    waiting_for_photos = State()

async def safe_delete_message(message):
    try:
        await message.delete()
    except Exception:
        pass

async def safe_edit_or_reply(callback: CallbackQuery, text: str, reply_markup=None, parse_mode="HTML"):
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        await safe_delete_message(callback.message)
        await callback.message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)

@router.callback_query(F.data.startswith("task:"))
async def show_task_card(callback: CallbackQuery, state: FSMContext):
    # Сохраняем контекст для возврата
    data = await state.get_data()
    prev_list_type = data.get("current_list_type")
    prev_page = data.get("current_page", 1)
    prev_sort = data.get("current_sort", "date")
    prev_filter = data.get("current_filter")
    await state.update_data(prev_list_type=prev_list_type, prev_page=prev_page, prev_sort=prev_sort, prev_filter=prev_filter)

    task_id = int(callback.data.split(":")[1])
    task = await get_task(task_id)
    if not task:
        await callback.answer("Заявка не найдена", show_alert=True)
        return
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Вы не зарегистрированы", show_alert=True)
        return
    if employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE):
        if task.assigned_to != employee.id and not (task.assigned_team == employee.team and task.assigned_to is None):
            await callback.answer("У вас нет доступа к этой заявке", show_alert=True)
            return
    status_emoji = get_task_status_emoji(task.status)
    text = (
        f"{status_emoji} <b>#{task.id} {task.title}</b>\n\n"
        f"📄 <b>Описание:</b>\n{task.description or '—'}\n\n"
        f"🏢 <b>Объект:</b> {task.building or '—'}, кв. {task.apartment or '—'}\n"
        f"🔢 <b>Приоритет:</b> {task.priority}\n"
        f"📊 <b>Статус:</b> {task.status}\n\n"
        f"👤 <b>Создал:</b> {task.creator.full_name if task.creator else '—'}\n"
        f"👥 <b>Исполнитель:</b> {task.assignee.full_name if task.assignee else 'не назначен'}\n"
        f"🕒 <b>Создана:</b> {task.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    )
    if task.wait_until:
        text += f"⏳ <b>Ожидание до:</b> {task.wait_until.strftime('%d.%m.%Y %H:%M')}\n"
    if task.closed_at:
        text += f"🔒 <b>Закрыта:</b> {task.closed_at.strftime('%d.%m.%Y %H:%M')}\n"

    await safe_edit_or_reply(callback, text, task_actions_keyboard(task, employee))
    await callback.answer()

@router.callback_query(F.data.startswith("task_take:"))
async def take_task_callback(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Вы не зарегистрированы", show_alert=True)
        return
    task = await take_task(task_id, employee.id)
    if not task:
        await callback.answer("Не удалось взять задачу. Возможно, она уже назначена другому.", show_alert=True)
        return
    await callback.answer("✅ Задача взята в работу")
    await show_task_card(callback, state)
    await notify_admins(f"📢 Сотрудник {employee.full_name} взял задачу #{task_id} в работу.")

@router.callback_query(F.data.startswith("task_pause:"))
async def pause_task(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    task = await get_task(task_id)
    if not task or task.assigned_to != employee.id:
        await callback.answer("Вы не исполнитель этой задачи", show_alert=True)
        return
    await state.update_data(task_id=task_id, action="pause")
    await safe_edit_or_reply(callback, "Выберите срок ожидания или введите время вручную:", waiting_time_keyboard(task_id))
    await callback.answer()

@router.callback_query(F.data.startswith("task_resume:"))
async def resume_task(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    task = await get_task(task_id)
    if not task or task.assigned_to != employee.id:
        await callback.answer("Вы не исполнитель этой задачи", show_alert=True)
        return
    # Возобновляем без комментария
    task = await change_status(task_id, "in_progress", employee.id)
    if task:
        await callback.answer("✅ Задача возобновлена")
        await show_task_card(callback, state)
    else:
        await callback.answer("❌ Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("task_status:"))
async def change_task_status(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split(":")
    task_id = int(parts[1])
    status_str = parts[2]
    status_map = {
        "accept": "accepted",
        "start": "in_progress",
        "check": "checking",
        "close": "closed",
        "rework": "in_progress",
        "pause": "paused",
        "resume": "in_progress",
    }
    new_status = status_map.get(status_str)
    if not new_status:
        await callback.answer("Неизвестный статус", show_alert=True)
        return
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Вы не зарегистрированы", show_alert=True)
        return
    task = await get_task(task_id)
    if not task:
        await callback.answer("Задача не найдена", show_alert=True)
        return
    # Проверка прав
    if employee.role in (UserRole.TECHNICIAN, UserRole.CLEANER, UserRole.SECURITY):
        if task.assigned_to != employee.id:
            await callback.answer("Вы не исполнитель этой задачи", show_alert=True)
            return
        if new_status not in ("accepted", "in_progress", "checking", "closed", "paused"):
            await callback.answer("Недопустимый статус", show_alert=True)
            return
    elif employee.role in (UserRole.CONCIERGE, UserRole.ADMIN, UserRole.DIRECTOR):
        if new_status not in ("closed", "in_progress"):
            await callback.answer("Недопустимый статус для вашей роли", show_alert=True)
            return
    else:
        await callback.answer("У вас нет прав", show_alert=True)
        return
    task = await change_status(task_id, new_status, employee.id)
    if not task:
        await callback.answer("Ошибка изменения статуса", show_alert=True)
        return
    await callback.answer(f"✅ Статус изменён на {new_status}")
    if new_status == "checking":
        await notify_concierges(f"🔍 Задача #{task_id} готова к проверке. Исполнитель: {employee.full_name}")
    elif new_status == "closed":
        await notify_concierges(f"✅ Задача #{task_id} закрыта. Проверил: {employee.full_name}")
    # Уведомление администраторам при приостановке или возврате
    if new_status == "paused":
        await notify_admins(f"⏸ Задача #{task_id} приостановлена исполнителем {employee.full_name}")
    elif new_status == "in_progress" and status_str == "rework":
        await notify_admins(f"🔄 Задача #{task_id} возвращена на доработку исполнителем {employee.full_name}")
    await show_task_card(callback, state)

# ... остальные обработчики комментариев, фото, истории, отложки (они уже есть) – я их не меняю, они остаются в файле, но для полноты дам полный файл с ними.
# Однако поскольку файл большой, я дам полный код отдельно (он уже был в предыдущих версиях).
# Я добавлю только изменения, но для простоты я дам полный файл card.py с исправлениями в следующем сообщении.
