from aiogram import Router, F, types
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
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
from app.keyboards.tasks import get_priority_emoji, get_priority_name
from app.keyboards.waiting import waiting_time_keyboard
from app.services.notification_service import notify_user, notify_admins, notify_concierges
from app.states.tasks.waiting import TaskWaiting
from app.states.tasks.photo import TaskAddPhoto
from app.metrics import bot_errors_total

router = Router()

class TaskCommentState(StatesGroup):
    waiting_for_comment = State()

class TaskPhotoState(StatesGroup):
    waiting_for_photos = State()

class TaskCheckState(StatesGroup):
    waiting_for_comment = State()
    waiting_for_photo = State()

async def safe_delete_message(message):
    try:
        await message.delete()
    except Exception:
        pass

async def safe_edit_or_reply(callback: CallbackQuery, text: str, reply_markup=None, parse_mode="HTML"):
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        bot_errors_total.labels(error_type=type(e).__name__).inc()
        await safe_delete_message(callback.message)
        await callback.message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)

@router.callback_query(F.data.startswith("task:"))
async def show_task_card(callback: CallbackQuery, state: FSMContext):
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
    priority_emoji = get_priority_emoji(task.priority)
    priority_name = get_priority_name(task.priority)

    # Формируем адрес
    address_parts = []
    if task.building:
        address_parts.append(f"корп. {task.building}")
    if task.entrance:
        address_parts.append(f"под. {task.entrance}")
    if task.floor:
        address_parts.append(f"эт. {task.floor}")
    if task.apartment:
        address_parts.append(f"кв. {task.apartment}")
    elif task.location_type == "common_area":
        address_parts.append("общая зона")
    elif task.location_type == "parking":
        if task.parking_level is not None and task.parking_spot is not None:
            address_parts.append(f"паркинг {task.parking_level} эт., место {task.parking_spot}")
    elif task.location_type == "cellar" and task.cellar is not None:
        address_parts.append(f"келлер {task.cellar}")
    address = ", ".join(address_parts) if address_parts else "—"

    # Формируем текст карточки
    text = f"{status_emoji} <b>#{task.id} {task.title}</b>\n\n"
    text += f"🔥 <b>Приоритет:</b> {priority_emoji} {priority_name}\n"
    text += f"📊 <b>Статус:</b> {status_emoji} {task.status}\n"
    text += f"🏢 <b>Адрес:</b> {address}\n\n"
    text += f"📄 <b>Описание:</b>\n{task.description or '—'}\n\n"
    text += f"👤 <b>Создал:</b> {task.creator.full_name if task.creator else '—'}\n"
    if task.assignee:
        text += f"👥 <b>Исполнитель:</b> {task.assignee.full_name}"
        if task.assignee.team:
            text += f" (команда: {task.assignee.team.value})"
        text += "\n"
    else:
        text += f"👥 <b>Исполнитель:</b> не назначен\n"
    text += f"📅 <b>Создана:</b> {task.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    # Дата назначения (если есть)
    if task.assigned_to and task.updated_at:
        text += f"📅 <b>Назначена:</b> {task.updated_at.strftime('%d.%m.%Y %H:%M')}\n"
    if task.closed_at:
        text += f"🔒 <b>Закрыта:</b> {task.closed_at.strftime('%d.%m.%Y %H:%M')}\n"
    if task.wait_until:
        text += f"⏳ <b>Ожидание до:</b> {task.wait_until.strftime('%d.%m.%Y %H:%M')}\n"
    # Вложения
    if task.photos:
        text += f"📷 Фото: {len(task.photos)} шт."
        if task.video_ids:
            text += f"  🎥 Видео: {len(task.video_ids)} шт."
        text += "\n"
    elif task.video_ids:
        text += f"🎥 Видео: {len(task.video_ids)} шт.\n"
    # Количество комментариев и записей истории
    if task.comments:
        text += f"💬 Комментарии: {len(task.comments)}"
    if task.history:
        text += f"  📜 История: {len(task.history)} записей"
    text += "\n"

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
    await safe_edit_or_reply(callback, "⏸ Выберите срок ожидания:", waiting_time_keyboard(task_id))
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
    task = await change_status(task_id, "in_progress", employee.id)
    if task:
        await callback.answer("✅ Задача возобновлена")
        await show_task_card(callback, state)
    else:
        await callback.answer("❌ Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("task_check_start:"))
async def start_check_task(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    task = await get_task(task_id)
    if not task or task.assigned_to != employee.id:
        await callback.answer("Вы не исполнитель", show_alert=True)
        return
    await state.update_data(task_id=task_id)
    await state.set_state(TaskCheckState.waiting_for_comment)
    await callback.message.delete()
    await callback.message.answer("✍️ Введите комментарий (обязательно):")
    await callback.answer()

@router.message(StateFilter(TaskCheckState.waiting_for_comment), F.text)
async def process_check_comment(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        await message.answer("Комментарий обязателен. Введите текст:")
        return
    await state.update_data(comment=text)
    await state.set_state(TaskCheckState.waiting_for_photo)
    await message.answer("🖼 Пришлите фото (опционально) или нажмите **Готово**:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="✅ Готово")]],
            resize_keyboard=True
        ))

@router.message(StateFilter(TaskCheckState.waiting_for_photo), F.photo)
async def process_check_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Добавлено фото ({len(photos)})")

@router.message(StateFilter(TaskCheckState.waiting_for_photo), F.text == "✅ Готово")
async def finish_check_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    task_id = data.get("task_id")
    comment = data.get("comment")
    photos = data.get("photos", [])
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка")
        await state.clear()
        return
    if comment:
        await add_comment(task_id, employee.id, comment)
    for file_id in photos:
        await add_photo(task_id, employee.id, file_id)
    task = await change_status(task_id, "checking", employee.id, comment)
    if task:
        await notify_concierges(f"🔍 Задача #{task_id} готова к проверке. Исполнитель: {employee.full_name}\nКомментарий: {comment}")
        await message.answer("✅ Задача отправлена на проверку")
        await message.answer(f"📋 Карточка задачи #{task_id}:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Посмотреть заявку", callback_data=f"task:{task_id}")]
        ]))
    else:
        await message.answer("❌ Ошибка изменения статуса")
    await state.clear()

@router.callback_query(F.data.startswith("task_status:"))
async def change_task_status(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    task_id = int(parts[1])
    status_str = parts[2]
    status_map = {
        "accept": "accepted",
        "start": "in_progress",
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
    elif new_status == "paused":
        await notify_admins(f"⏸ Задача #{task_id} приостановлена исполнителем {employee.full_name}")
    elif new_status == "in_progress" and status_str == "rework":
        await notify_admins(f"🔄 Задача #{task_id} возвращена на доработку исполнителем {employee.full_name}")
    await show_task_card(callback, state)

# ========== Комментарии ==========
@router.callback_query(F.data.startswith("task_comment_list:"))
async def show_comments(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    task = await get_task(task_id)
    if not task:
        await callback.answer("Задача не найдена", show_alert=True)
        return
    comments = task.comments
    if not comments:
        text = "💬 Комментариев пока нет."
    else:
        text = f"💬 <b>Комментарии к задаче #{task_id}</b>\n\n"
        for c in comments:
            user_name = c.author.full_name if c.author else "—"
            text += f"👤 {user_name} | {c.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            text += f"{c.text}\n\n"
    await safe_delete_message(callback.message)
    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Добавить комментарий", callback_data=f"task_comment_add:{task_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"task_comment_back:{task_id}")],
        ])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("task_comment_add:"))
async def start_add_comment(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Вы не зарегистрированы", show_alert=True)
        return
    await state.set_state(TaskCommentState.waiting_for_comment)
    await state.update_data(task_id=task_id)
    await safe_delete_message(callback.message)
    await callback.message.answer("✍️ Введите текст комментария:")
    await callback.answer()

@router.message(StateFilter(TaskCommentState.waiting_for_comment), F.text)
async def process_add_comment(message: Message, state: FSMContext):
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
    await message.answer("💬 Комментарии:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Посмотреть комментарии", callback_data=f"task_comment_list:{task_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"task_comment_back:{task_id}")],
    ]))

@router.callback_query(F.data.startswith("task_comment_back:"))
async def comment_back_to_task(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    await safe_delete_message(callback.message)
    await show_task_card(callback, state)
    await callback.answer()

# ========== История (исправлена сортировка: сначала старые) ==========
@router.callback_query(F.data.startswith("task_history:"))
async def show_task_history(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    history = await get_task_history(task_id)
    if not history:
        await callback.answer("История пуста", show_alert=True)
        return
    # Переворачиваем: сначала старые записи, потом новые
    history = list(reversed(history))
    text = f"📜 <b>История задачи #{task_id}</b>\n\n"
    for entry in history[:5]:
        user_name = entry.user.full_name if entry.user else "—"
        text += f"🕒 {entry.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        text += f"👤 {user_name}\n"
        text += f"📌 {entry.action}\n"
        text += f"📝 {entry.description}\n\n"
    await safe_delete_message(callback.message)
    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📜 Показать все", callback_data=f"task_history_all:{task_id}")],
            [InlineKeyboardButton(text="⬅️ Назад в карточку", callback_data=f"task_history_back:{task_id}")],
        ])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("task_history_all:"))
async def show_all_history(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    history = await get_task_history(task_id)
    if not history:
        await callback.answer("История пуста", show_alert=True)
        return
    # Переворачиваем: сначала старые
    history = list(reversed(history))
    text = f"📜 <b>Вся история задачи #{task_id}</b>\n\n"
    for entry in history:
        user_name = entry.user.full_name if entry.user else "—"
        text += f"🕒 {entry.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        text += f"👤 {user_name}\n"
        text += f"📌 {entry.action}\n"
        text += f"📝 {entry.description}\n\n"
    await safe_delete_message(callback.message)
    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в карточку", callback_data=f"task_history_back:{task_id}")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("task_history_back:"))
async def history_back_to_task(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    await safe_delete_message(callback.message)
    await show_task_card(callback, state)
    await callback.answer()

# ========== Фото и видео ==========
@router.callback_query(F.data.startswith("task_video:"))
async def show_task_videos(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    task = await get_task(task_id)
    if not task or not task.video_ids:
        await callback.answer("Нет видео", show_alert=True)
        return
    await safe_delete_message(callback.message)
    for video_id in task.video_ids:
        await callback.message.answer_video(video_id)
    await callback.message.answer(
        "⬅️ Назад",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"task:{task_id}")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("task_photo:"))
async def show_task_photos(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    task = await get_task(task_id)
    if not task or not task.photos:
        await callback.answer("Нет фото", show_alert=True)
        return
    if len(task.photos) == 1:
        photo = task.photos[0]
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"task:{task_id}")]
        ])
        await safe_delete_message(callback.message)
        await callback.message.answer_photo(photo.telegram_file_id, reply_markup=kb)
        await callback.answer()
        return
    buttons = []
    for i, _ in enumerate(task.photos):
        buttons.append([InlineKeyboardButton(text=f"📷 Фото {i+1}", callback_data=f"task_photo_view:{task_id}:{i}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"task:{task_id}")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await safe_delete_message(callback.message)
    await callback.message.answer("📷 Выберите фото для просмотра:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("task_photo_view:"))
async def view_task_photo(callback: CallbackQuery, state: FSMContext):
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
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад к списку фото", callback_data=f"task_photo_back:{task_id}")]
    ])
    await safe_delete_message(callback.message)
    await callback.message.answer_photo(
        photo.telegram_file_id,
        caption=f"📷 Фото {index+1}/{len(task.photos)}",
        reply_markup=kb
    )
    await callback.answer()

@router.callback_query(F.data.startswith("task_photo_back:"))
async def back_to_task_photos(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    task = await get_task(task_id)
    if not task or not task.photos:
        await callback.answer("Нет фото", show_alert=True)
        return
    buttons = []
    for i, _ in enumerate(task.photos):
        buttons.append([InlineKeyboardButton(text=f"📷 Фото {i+1}", callback_data=f"task_photo_view:{task_id}:{i}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"task:{task_id}")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await safe_delete_message(callback.message)
    await callback.message.answer("📷 Выберите фото для просмотра:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("task_add_photo:"))
async def start_add_photo(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Вы не зарегистрированы", show_alert=True)
        return
    task = await get_task(task_id)
    if not task:
        await callback.answer("Задача не найдена", show_alert=True)
        return
    if employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE) and task.assigned_to != employee.id:
        await callback.answer("У вас нет прав добавлять фото", show_alert=True)
        return
    await state.set_state(TaskPhotoState.waiting_for_photos)
    await state.update_data(task_id=task_id)
    await safe_delete_message(callback.message)
    await callback.message.answer(
        "📷 Отправьте фото (или несколько). После отправки нажмите **Готово**:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="✅ Готово")]],
            resize_keyboard=True
        )
    )
    await callback.answer()

@router.message(StateFilter(TaskPhotoState.waiting_for_photos), F.photo)
async def process_add_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Фото добавлено ({len(photos)})")

@router.message(StateFilter(TaskPhotoState.waiting_for_photos), F.text == "✅ Готово")
async def finish_add_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    task_id = data.get("task_id")
    photos = data.get("photos", [])
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка")
        await state.clear()
        return
    if not photos:
        await message.answer("Нет фото для добавления.")
        await state.clear()
        return
    for file_id in photos:
        await add_photo(task_id, employee.id, file_id)
    await message.answer(f"✅ Добавлено {len(photos)} фото к задаче #{task_id}.")
    await state.clear()
    task = await get_task(task_id)
    if task:
        await message.answer(f"📋 Карточка задачи #{task_id}", reply_markup=task_actions_keyboard(task, employee))
    else:
        await message.answer("Возврат в меню.")

# ========== Ожидание (исправлено: добавлен комментарий в задачу) ==========
@router.callback_query(F.data.startswith("task_wait:"))
async def start_wait(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    task = await get_task(task_id)
    if not employee or task.assigned_to != employee.id:
        await callback.answer("Вы не исполнитель этой задачи", show_alert=True)
        return
    await state.update_data(task_id=task_id)
    await safe_edit_or_reply(callback, "⏸ Выберите срок ожидания:", waiting_time_keyboard(task_id))
    await callback.answer()

@router.callback_query(F.data.startswith("wait_time:"))
async def waiting_time_selected(callback: CallbackQuery, state: FSMContext):
    _, task_id_str, hours_str = callback.data.split(":")
    task_id = int(task_id_str)
    hours = int(hours_str)
    await state.update_data(task_id=task_id, hours=hours)
    await state.set_state(TaskWaiting.comment)
    await safe_delete_message(callback.message)
    await callback.message.answer(
        "✍️ Введите комментарий (обязательно):",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True
        )
    )
    await callback.answer()

@router.message(TaskWaiting.comment, F.text != "❌ Отмена")
async def process_wait_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    task_id = data.get("task_id")
    hours = data.get("hours")
    comment = message.text.strip()
    if not comment:
        await message.answer("Комментарий обязателен. Введите текст:")
        return
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка")
        await state.clear()
        return
    # Добавляем комментарий в задачу
    await add_comment(task_id, employee.id, comment)
    wait_until = datetime.utcnow() + timedelta(hours=hours)
    task = await change_status(task_id, "waiting", employee.id, comment, wait_until)
    if task:
        await message.answer(
            f"✅ Задача отложена до {wait_until.strftime('%d.%m.%Y %H:%M')}",
            reply_markup=ReplyKeyboardRemove()
        )
        await notify_concierges(f"⏳ Задача #{task_id} отложена до {wait_until.strftime('%d.%m.%Y %H:%M')}. Комментарий: {comment}")
        await message.answer(f"📋 Карточка задачи #{task_id}:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Посмотреть заявку", callback_data=f"task:{task_id}")]
        ]))
    else:
        await message.answer("❌ Ошибка при откладывании задачи")
    await state.clear()

@router.message(TaskWaiting.comment, F.text == "❌ Отмена")
async def cancel_wait_comment(message: Message, state: FSMContext):
    await state.clear()
    employee = await get_employee(message.from_user.id)
    if employee:
        await message.answer("❌ Отменено", reply_markup=ReplyKeyboardRemove())
        data = await state.get_data()
        task_id = data.get("task_id")
        if task_id:
            await message.answer(f"📋 Карточка задачи #{task_id}:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 Посмотреть заявку", callback_data=f"task:{task_id}")]
            ]))
        else:
            await message.answer("Главное меню", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Отменено")
