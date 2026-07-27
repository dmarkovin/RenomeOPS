from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter
from datetime import datetime, timedelta

from app.services.employees.service import get_employee, get_employee_by_id
from app.services.passes.service import (
    create_pass, get_pass, get_passes, get_pass_history, search_passes,
    check_in, check_out, update_pass_status
)
from app.services.tasks.service import get_available_employees, get_teams_with_members
from app.database.models import UserRole, Team
from app.keyboards.passes import (
    pass_list_keyboard, pass_action_keyboard, pass_main_menu_keyboard,
    pass_assign_type_keyboard
)
from app.keyboards.assign import employee_selection_keyboard
from app.keyboards.date_picker import date_selection_keyboard
from app.keyboards.main_menu import main_menu_keyboard
from app.services.notification_service import notify_user, notify_concierges, notify_security, notify_team

router = Router()

class PassCreate(StatesGroup):
    type = State()
    guest_name = State()
    car_number = State()
    purpose = State()
    start_date = State()
    end_date = State()
    assign_type = State()
    assign_employee = State()
    comment = State()
    confirm = State()
    select_start_date = State()
    select_end_date = State()

class PassSearch(StatesGroup):
    query = State()

# ========== Главное меню пропусков ==========
@router.message(F.text == "🚗 Пропуска")
async def passes_menu(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE, UserRole.SECURITY):
        await message.answer("У вас нет прав.")
        return
    await message.answer("🚗 Меню пропусков:", reply_markup=pass_main_menu_keyboard())

# ========== Создание пропуска ==========
@router.message(F.text == "➕ Заказать пропуск")
async def start_create_pass(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE):
        await message.answer("Нет прав.")
        return
    await state.clear()
    await state.set_state(PassCreate.type)
    await message.answer("Выберите тип пропуска:", reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="👤 Гость")],
            [types.KeyboardButton(text="🚗 Автомобиль")],
            [types.KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    ))

@router.message(PassCreate.type)
async def process_type(message: Message, state: FSMContext):
    text = message.text
    if text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено", reply_markup=pass_main_menu_keyboard())
        return
    if text not in ("👤 Гость", "🚗 Автомобиль"):
        await message.answer("Пожалуйста, выберите кнопкой.")
        return
    await state.update_data(type="guest" if text == "👤 Гость" else "car")
    await state.set_state(PassCreate.guest_name if text == "👤 Гость" else PassCreate.car_number)
    if text == "👤 Гость":
        await message.answer("Введите имя гостя:", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Введите номер автомобиля:", reply_markup=ReplyKeyboardRemove())

@router.message(PassCreate.guest_name)
async def process_guest_name(message: Message, state: FSMContext):
    await state.update_data(guest_name=message.text.strip())
    await state.set_state(PassCreate.purpose)
    await message.answer("Введите цель визита (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(PassCreate.car_number)
async def process_car_number(message: Message, state: FSMContext):
    await state.update_data(car_number=message.text.strip())
    await state.set_state(PassCreate.purpose)
    await message.answer("Введите цель визита (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(PassCreate.purpose)
async def process_purpose(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(purpose=text if text != "-" else "")
    await state.set_state(PassCreate.select_start_date)
    await message.answer("Выберите дату начала действия пропуска:", reply_markup=date_selection_keyboard("start"))

@router.callback_query(StateFilter(PassCreate.select_start_date), F.data.startswith("date_start:"))
async def process_start_date(callback: CallbackQuery, state: FSMContext):
    date_str = callback.data.split(":")[1]
    try:
        start_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        await callback.answer("Неверный формат даты", show_alert=True)
        return
    await state.update_data(start_date=start_date)
    await state.set_state(PassCreate.select_end_date)
    await callback.message.edit_text("Выберите дату окончания действия пропуска:", reply_markup=date_selection_keyboard("end"))
    await callback.answer()

@router.callback_query(StateFilter(PassCreate.select_start_date), F.data == "date_start_manual")
async def start_date_manual(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PassCreate.start_date)
    await callback.message.edit_text("Введите дату начала в формате ДД.ММ.ГГГГ (например, 01.01.2025):")
    await callback.answer()

@router.message(PassCreate.start_date)
async def process_start_date_manual(message: Message, state: FSMContext):
    text = message.text.strip()
    try:
        start_date = datetime.strptime(text, "%d.%m.%Y")
    except ValueError:
        await message.answer("Неверный формат. Используйте ДД.ММ.ГГГГ (например, 01.01.2025).")
        return
    await state.update_data(start_date=start_date)
    await state.set_state(PassCreate.select_end_date)
    await message.answer("Выберите дату окончания действия пропуска:", reply_markup=date_selection_keyboard("end"))

@router.callback_query(StateFilter(PassCreate.select_end_date), F.data.startswith("date_end:"))
async def process_end_date(callback: CallbackQuery, state: FSMContext):
    date_str = callback.data.split(":")[1]
    try:
        end_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        await callback.answer("Неверный формат даты", show_alert=True)
        return
    data = await state.get_data()
    start_date = data.get("start_date")
    if end_date < start_date:
        await callback.answer("Дата окончания не может быть раньше даты начала.", show_alert=True)
        return
    await state.update_data(end_date=end_date)
    await state.set_state(PassCreate.assign_type)
    await callback.message.delete()
    await callback.message.answer("Выберите, кому назначить пропуск:", reply_markup=pass_assign_type_keyboard())
    await callback.answer()

@router.callback_query(StateFilter(PassCreate.select_end_date), F.data == "date_end_manual")
async def end_date_manual(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PassCreate.end_date)
    await callback.message.edit_text("Введите дату окончания в формате ДД.ММ.ГГГГ (например, 01.01.2025):")
    await callback.answer()

@router.message(PassCreate.end_date)
async def process_end_date_manual(message: Message, state: FSMContext):
    text = message.text.strip()
    try:
        end_date = datetime.strptime(text, "%d.%m.%Y")
    except ValueError:
        await message.answer("Неверный формат. Используйте ДД.ММ.ГГГГ (например, 01.01.2025).")
        return
    data = await state.get_data()
    start_date = data.get("start_date")
    if end_date < start_date:
        await message.answer("Дата окончания не может быть раньше даты начала.")
        return
    await state.update_data(end_date=end_date)
    await state.set_state(PassCreate.assign_type)
    await message.answer("Выберите, кому назначить пропуск:", reply_markup=pass_assign_type_keyboard())

# ---- Обработчики выбора типа назначения ----
@router.message(StateFilter(PassCreate.assign_type), F.text.in_(["👥 Всей охране", "👤 Конкретному сотруднику", "⏭ Пропустить"]))
async def process_assign_type(message: Message, state: FSMContext):
    text = message.text
    if text == "⏭ Пропустить":
        await state.update_data(assigned_to=None, assigned_team=None)
        await state.set_state(PassCreate.comment)
        await message.answer("Введите комментарий (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())
        return
    if text == "👥 Всей охране":
        await state.update_data(assigned_to=None, assigned_team=Team.TEAM_SECURITY)
        await state.set_state(PassCreate.comment)
        await message.answer("Пропуск будет назначен всей охране. Введите комментарий (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())
        return
    if text == "👤 Конкретному сотруднику":
        employees = await get_available_employees(role=UserRole.SECURITY)
        if not employees:
            await message.answer("Нет доступных сотрудников охраны. Выберите другой вариант.")
            return
        await state.set_state(PassCreate.assign_employee)
        await message.answer("Выберите сотрудника охраны:", reply_markup=employee_selection_keyboard(employees, "pass_assign", 0))
        return

@router.message(StateFilter(PassCreate.assign_type))
async def invalid_assign_type(message: Message):
    await message.answer("Пожалуйста, используйте кнопки для выбора.")

# ---- Обработчик выбора конкретного сотрудника ----
@router.callback_query(StateFilter(PassCreate.assign_employee), F.data.startswith("pass_assign_emp:"))
async def assign_employee_final(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.message.answer("Ошибка формата")
        return
    _, emp_id_str, _ = parts
    emp_id = int(emp_id_str)
    await state.update_data(assigned_to=emp_id, assigned_team=None)
    await callback.message.delete()
    await callback.message.answer("✅ Охрана назначена.")
    await state.set_state(PassCreate.comment)
    await callback.message.answer("Введите комментарий (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

# ---- Комментарий и подтверждение ----
@router.message(StateFilter(PassCreate.comment), F.text)
async def process_comment(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(comment=text if text != "-" else "")
    await state.set_state(PassCreate.confirm)
    data = await state.get_data()
    assigned_to = data.get('assigned_to')
    assigned_team = data.get('assigned_team')
    if assigned_to:
        assignee = await get_employee_by_id(assigned_to)
        executor_text = assignee.full_name if assignee else "назначен"
    elif assigned_team:
        executor_text = f"команда {assigned_team.value}"
    else:
        executor_text = "не назначен"
    text = (
        f"📝 Проверьте данные пропуска:\n\n"
        f"Тип: {data.get('type')}\n"
        f"Гость: {data.get('guest_name') or '—'}\n"
        f"Авто: {data.get('car_number') or '—'}\n"
        f"Цель: {data.get('purpose') or '—'}\n"
        f"Начало: {data.get('start_date').strftime('%d.%m.%Y') if data.get('start_date') else '—'}\n"
        f"Окончание: {data.get('end_date').strftime('%d.%m.%Y') if data.get('end_date') else '—'}\n"
        f"Исполнитель: {executor_text}\n"
        f"Комментарий: {data.get('comment') or '—'}\n\n"
        f"Подтвердить создание?"
    )
    await message.answer(text, reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Да, создать")], [KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))

@router.message(StateFilter(PassCreate.confirm), F.text == "✅ Да, создать")
async def confirm_create_pass(message: Message, state: FSMContext):
    data = await state.get_data()
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка.")
        await state.clear()
        return
    try:
        p = await create_pass(
            type=data.get("type"),
            guest_name=data.get("guest_name"),
            car_number=data.get("car_number"),
            purpose=data.get("purpose"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            comment=data.get("comment"),
            photo_ids=[],
            created_by=employee.id,
            assigned_to=data.get("assigned_to"),
            assigned_team=data.get("assigned_team")
        )
        await state.clear()
        if p.assigned_to:
            guard = await get_employee_by_id(p.assigned_to)
            if guard and guard.telegram_id:
                await notify_user(guard.telegram_id, f"🪪 Вам назначен пропуск #{p.id}.")
        elif p.assigned_team:
            await notify_team(p.assigned_team, f"🪪 Новый пропуск #{p.id} назначен на вашу команду.")
        await notify_concierges(f"🪪 Создан новый пропуск #{p.id} для {p.guest_name or p.car_number}.")
        await notify_security(f"🪪 Создан новый пропуск #{p.id} для {p.guest_name or p.car_number}.")
        await message.answer(f"✅ Пропуск #{p.id} создан!", reply_markup=pass_main_menu_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", parse_mode=None)
        await state.clear()

@router.message(StateFilter(PassCreate.confirm), F.text == "❌ Отмена")
async def cancel_confirm(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено", reply_markup=pass_main_menu_keyboard())

# ========== Активные пропуски ==========
@router.message(F.text == "📋 Активные пропуски")
async def list_active_passes(message: Message, page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    limit = 10
    offset = (page - 1) * limit
    if employee.role == UserRole.SECURITY:
        passes = await get_passes(assigned_to=employee.id, status='active', limit=limit, offset=offset)
    else:
        passes = await get_passes(status='active', limit=limit, offset=offset)
    total = len(passes)
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    if not passes:
        await message.answer("Нет активных пропусков.")
        return
    text = "📋 Активные пропуски:\n\n"
    for p in passes:
        status_emoji = "🟢" if p.status == "active" else "🔵" if p.status == "used" else "🔴"
        label = p.guest_name or p.car_number or "—"
        text += f"{status_emoji} #{p.id} {label} ({p.type}) – {p.status}\n"
    await message.answer(text, reply_markup=pass_list_keyboard(passes, page, total_pages))

# ========== История пропусков ==========
@router.message(F.text == "📜 История пропусков")
async def list_history(message: Message, page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    limit = 10
    offset = (page - 1) * limit
    passes = await get_passes(status__in=['used', 'expired', 'completed'], limit=limit, offset=offset)
    total = len(passes)
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    if not passes:
        await message.answer("История пуста.")
        return
    text = "📜 История пропусков:\n\n"
    for p in passes:
        status_emoji = "🔵" if p.status == "used" else "🔴" if p.status == "expired" else "✅" if p.status == "completed" else "⚪"
        label = p.guest_name or p.car_number or "—"
        text += f"{status_emoji} #{p.id} {label} ({p.type}) – {p.status}\n"
    await message.answer(text, reply_markup=pass_list_keyboard(passes, page, total_pages))

# ========== Поиск по пропускам ==========
@router.message(F.text == "🔍 Поиск по пропускам")
async def start_search_pass(message: Message, state: FSMContext):
    await state.set_state(PassSearch.query)
    await message.answer("Введите текст для поиска (имя гостя, номер авто, ID):")

@router.message(StateFilter(PassSearch.query))
async def process_search_pass(message: Message, state: FSMContext):
    query = message.text.strip()
    if len(query) < 2:
        await message.answer("Введите минимум 2 символа.")
        return
    passes = await search_passes(query, limit=20)
    if not passes:
        await message.answer("Ничего не найдено.")
        await state.clear()
        return
    text = "🔍 Результаты поиска по пропускам:\n\n"
    for p in passes:
        status_emoji = "🟢" if p.status == "active" else "🔵" if p.status == "used" else "🔴" if p.status == "expired" else "✅" if p.status == "completed" else "⚪"
        label = p.guest_name or p.car_number or "—"
        text += f"{status_emoji} #{p.id} {label} ({p.type}) – {p.status}\n"
    await message.answer(text)
    await state.clear()

# ========== Карточка пропуска ==========
@router.callback_query(F.data.startswith("pass:"))
async def show_pass_card(callback: CallbackQuery):
    pass_id = int(callback.data.split(":")[1])
    p = await get_pass(pass_id)
    if not p:
        await callback.answer("Не найден", show_alert=True)
        return
    employee = await get_employee(callback.from_user.id)
    user_role = employee.role.value if employee else None
    text = (
        f"🪪 Пропуск #{p.id}\n"
        f"Тип: {p.type}\n"
        f"Гость: {p.guest_name or '—'}\n"
        f"Авто: {p.car_number or '—'}\n"
        f"Цель: {p.purpose or '—'}\n"
        f"Начало: {p.start_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"Окончание: {p.end_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"Статус: {p.status}\n"
        f"Въезд: {p.checked_in_at.strftime('%d.%m.%Y %H:%M') if p.checked_in_at else '—'}\n"
        f"Выезд: {p.checked_out_at.strftime('%d.%m.%Y %H:%M') if p.checked_out_at else '—'}\n"
        f"Комментарий: {p.comment or '—'}"
    )
    history_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 История", callback_data=f"pass_history:{p.id}")]
    ])
    kb = pass_action_keyboard(p.id, p.status, user_role)
    merged_buttons = kb.inline_keyboard + history_kb.inline_keyboard
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=merged_buttons))
    await callback.answer()

@router.callback_query(F.data.startswith("pass_history:"))
async def show_pass_history(callback: CallbackQuery):
    pass_id = int(callback.data.split(":")[1])
    history = await get_pass_history(pass_id)
    if not history:
        await callback.answer("История пуста", show_alert=True)
        return
    text = f"📜 История пропуска #{pass_id}:\n\n"
    for entry in history[:10]:
        action = entry.action
        user = await get_employee_by_id(entry.user_id) if entry.user_id else None
        user_name = user.full_name if user else "Система"
        text += f"🕒 {entry.created_at.strftime('%d.%m.%Y %H:%M')} – {user_name}: {action}\n"
    await callback.message.answer(text)
    await callback.answer()

# ========== Действия с пропуском ==========
@router.callback_query(F.data.startswith("pass_checkin:"))
async def pass_checkin(callback: CallbackQuery):
    pass_id = int(callback.data.split(":")[1])
    p = await check_in(pass_id)
    if p:
        await callback.answer("✅ Въезд отмечен")
        await show_pass_card(callback)
    else:
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("pass_checkout:"))
async def pass_checkout(callback: CallbackQuery):
    pass_id = int(callback.data.split(":")[1])
    p = await check_out(pass_id)
    if p:
        await callback.answer("✅ Выезд отмечен")
        await show_pass_card(callback)
    else:
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("pass_complete:"))
async def pass_complete(callback: CallbackQuery):
    pass_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee or employee.role not in (UserRole.CONCIERGE, UserRole.ADMIN, UserRole.DIRECTOR):
        await callback.answer("Только для консьержа/админа/директора", show_alert=True)
        return
    p = await update_pass_status(pass_id, "completed")
    if p:
        await callback.answer("✅ Пропуск выполнен")
        await show_pass_card(callback)
    else:
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("pass_close:"))
async def pass_close(callback: CallbackQuery):
    pass_id = int(callback.data.split(":")[1])
    p = await update_pass_status(pass_id, "expired")
    if p:
        await callback.answer("✅ Пропуск закрыт")
        await show_pass_card(callback)
    else:
        await callback.answer("Ошибка", show_alert=True)

# ========== Пагинация и возврат ==========
@router.callback_query(F.data.startswith("pass_page:"))
async def paginate_passes(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    await callback.message.delete()
    await list_active_passes(callback.message, page)
    await callback.answer()

@router.callback_query(F.data == "pass_back")
async def back_to_pass_list(callback: CallbackQuery):
    await callback.message.delete()
    await list_active_passes(callback.message, 1)
    await callback.answer()

@router.callback_query(F.data == "pass_menu_back")
async def back_to_pass_menu(callback: CallbackQuery):
    await callback.message.delete()
    employee = await get_employee(callback.from_user.id)
    await callback.message.answer("🚗 Меню пропусков:", reply_markup=pass_main_menu_keyboard())
    await callback.answer()

@router.message(F.text == "⬅️ Назад")
async def back_from_pass_menu(message: Message):
    employee = await get_employee(message.from_user.id)
    await message.answer("Главное меню:", reply_markup=main_menu_keyboard(employee.role) if employee else None)

@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("Действие отменено")
    employee = await get_employee(callback.from_user.id)
    if employee:
        await callback.message.answer("🚗 Меню пропусков:", reply_markup=pass_main_menu_keyboard())
