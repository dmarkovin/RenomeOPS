from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, F, types
from aiogram.types import CallbackQuery, Message
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
from app.database.models import UserRole, TaskStatus
from app.keyboards.task_actions import task_actions_keyboard, get_task_status_emoji
from app.keyboards.waiting import waiting_time_keyboard
from app.services.notification_service import notify_user, notify_admins, notify_concierges
from app.states.tasks.waiting import TaskWaiting

router = Router()

class TaskCommentState(StatesGroup):
    waiting_for_comment = State()

class TaskPhotoState(StatesGroup):
    waiting_for_photos = State()

@router.callback_query(F.data.startswith("task:"))
async def show_task_card(callback: CallbackQuery):
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
        f"📊 <b>Статус:</b> {task.status.value}\n\n"
        f"👤 <b>Создал:</b> {task.creator.full_name if task.creator else '—'}\n"
        f"👥 <b>Исполнитель:</b> {task.assignee.full_name if task.assignee else 'не назначен'}\n"
        f"🕒 <b>Создана:</b> {task.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    )
    if task.wait_until:
        text += f"⏳ <b>Ожидание до:</b> {task.wait_until.strftime('%d.%m.%Y %H:%M')}\n"
    if task.closed_at:
        text += f"🔒 <b>Закрыта:</b> {task.closed_at.strftime('%d.%m.%Y %H:%M')}\n"

    await callback.message.edit_text(
        text,
        reply_markup=task_actions_keyboard(task, employee),
        parse_mode="HTML",
    )
    await callback.answer()

@router.callback_query(F.data.startswith("task_take:"))
async def take_task_callback(callback: CallbackQuery):
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
    await show_task_card(callback)
    await notify_admins(f"📢 Сотрудник {employee.full_name} взял задачу #{task_id} в работу.")

@router.callback_query(F.data.startswith("task_status:"))
@router.callback_query(F.data.startswith("task_status:"))
async def change_task_status(callback: CallbackQuery):
    await callback.answer()  # Сразу отвечаем, чтобы избежать таймаута
    parts = callback.data.split(":")
    task_id = int(parts[1])
    status_str = parts[2]
    status_map = {
        "accept": TaskStatus.ACCEPTED,
        "start": TaskStatus.IN_PROGRESS,
        "check": TaskStatus.CHECKING,
        "close": TaskStatus.CLOSED,
        "rework": TaskStatus.IN_PROGRESS,
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
    if employee.role in (UserRole.TECHNICIAN, UserRole.CLEANER, UserRole.SECURITY):
        if task.assigned_to != employee.id:
            await callback.answer("Вы не исполнитель этой задачи", show_alert=True)
            return
        if new_status not in (TaskStatus.ACCEPTED, TaskStatus.IN_PROGRESS, TaskStatus.CHECKING, TaskStatus.CLOSED):
            await callback.answer("Недопустимый статус", show_alert=True)
            return
    elif employee.role in (UserRole.CONCIERGE, UserRole.ADMIN, UserRole.DIRECTOR):
        if new_status not in (TaskStatus.CLOSED, TaskStatus.IN_PROGRESS):
            await callback.answer("Недопустимый статус для вашей роли", show_alert=True)
            return
    else:
        await callback.answer("У вас нет прав", show_alert=True)
        return
    task = await change_status(task_id, new_status, employee.id)
    if not task:
        await callback.answer("Ошибка изменения статуса", show_alert=True)
        return
    await callback.answer(f"✅ Статус изменён на {new_status.value}")
    if new_status == TaskStatus.CHECKING:
        await notify_concierges(f"🔍 Задача #{task_id} готова к проверке. Исполнитель: {employee.full_name}")
    elif new_status == TaskStatus.CLOSED:
        await notify_concierges(f"✅ Задача #{task_id} закрыта. Проверил: {employee.full_name}")
    await show_task_card(callback)

async def start_comment(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    await state.set_state(TaskCommentState.waiting_for_comment)
    await state.update_data(task_id=task_id)
    await callback.message.answer("✍️ Введите текст комментария:")
    await callback.answer()

@router.message(StateFilter(TaskCommentState.waiting_for_comment), F.text)
async def process_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    task_id = data.get("task_id")
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы")
        await state.clear()
        return
    comment = await add_comment(task_id, employee.id, message.text)
    if comment:
        await message.answer("✅ Комментарий добавлен.")
    else:
        await message.answer("❌ Ошибка добавления комментария.")
    await state.clear()


@router.callback_query(F.data.startswith("task_invoice:"))
async def task_invoice(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee or employee.role != UserRole.CONCIERGE:
        await callback.answer("Только для консьержей.", show_alert=True)
        return
    await callback.message.answer("🧾 Раздел выставления счетов находится в разработке.")
    await callback.answer()

@router.callback_query(F.data.startswith("task_photo_view:"))
async def view_task_photo(callback: CallbackQuery, state: FSMContext):
    """Показать конкретное фото по индексу"""
    parts = callback.data.split(":")
    task_id = int(parts[1])
    index = int(parts[2])
    task = await get_task(task_id)
    if not task or not task.photos:
        await callback.answer("Нет фото", show_alert=True)
        return
    if index >= len(task.photos):
        await callback.answer("Фото не найдено", show_alert=True)
        return
    photo = task.photos[index]
    # Клавиатура для навигации
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"task_photo_back:{task_id}")]
    ])
    await callback.message.delete()
    await callback.message.answer_photo(
        photo.telegram_file_id,
        caption=f"📷 Фото {index+1}/{len(task.photos)}",
        reply_markup=kb
    )
    await callback.answer()

@router.callback_query(F.data.startswith("task_photo_back:"))
async def back_to_task_photos(callback: CallbackQuery):
    """Вернуться к выбору фото"""
    task_id = int(callback.data.split(":")[1])
    await show_task_card(callback)  # переиспользуем существующий показ карточки
    await callback.answer()
