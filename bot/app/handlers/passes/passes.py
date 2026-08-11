from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter
from datetime import datetime, timedelta

from app.services.employees.service import get_employee, get_employee_by_id
from app.services.passes.service import (
    create_pass, get_pass, get_passes, get_pass_history, search_passes,
    check_in, check_out, update_pass_status, count_passes_by_status
)
from app.services.tasks.service import get_available_employees
from app.database.models import UserRole, Team
from app.keyboards.passes import (
    pass_list_keyboard, pass_action_keyboard, pass_main_menu_keyboard,
    pass_assign_type_keyboard
)
from app.keyboards.assign import employee_selection_keyboard
from app.keyboards.date_picker import date_selection_keyboard
from app.keyboards.main_menu import main_menu_keyboard
from app.services.notification_service import notify_user, notify_concierges, notify_security, notify_team
from app.database import AsyncSessionLocal

router = Router()

class PassCreate(StatesGroup):
    type = State()
    guest_name = State()
    car_number = State()
    apartment = State()
    purpose = State()
    start_date = State()
    end_date = State()
    assign_type = State()
    assign_employee = State()
    confirm = State()
    select_start_date = State()
    select_end_date = State()

class PassCommentState(StatesGroup):
    waiting_for_comment = State()

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
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE, UserRole.SECURITY):
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
    await state.set_state(PassCreate.apartment)
    await message.answer("Введите номер квартиры (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(PassCreate.car_number)
async def process_car_number(message: Message, state: FSMContext):
    await state.update_data(car_number=message.text.strip())
    await state.set_state(PassCreate.apartment)
    await message.answer("Введите номер квартиры (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(PassCreate.apartment)
async def process_apartment(message: Message, state: FSMContext):
    text = message.text.strip()
    if text.isdigit():
        await state.update_data(apartment=int(text))
    else:
        await state.update_data(apartment=None)
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
    await callback.message.edit_text(
        "Введите дату начала в формате ДД.ММ.ГГГГ (например, 01.01.2025):",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅ Назад")]],
            resize_keyboard=True
        )
    )
    await callback.answer()

@router.message(PassCreate.start_date)
async def process_start_date_manual(message: Message, state: FSMContext):
    text = message.text.strip()
    if text == "⬅ Назад":
        await state.set_state(PassCreate.select_start_date)
        await message.answer("Выберите дату начала:", reply_markup=date_selection_keyboard("start"))
        return
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
    await callback.message.edit_text(
        "Введите дату окончания в формате ДД.ММ.ГГГГ (например, 01.01.2025):",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅ Назад")]],
            resize_keyboard=True
        )
    )
    await callback.answer()

@router.message(PassCreate.end_date)
async def process_end_date_manual(message: Message, state: FSMContext):
    text = message.text.strip()
    if text == "⬅ Назад":
        await state.set_state(PassCreate.select_end_date)
        await message.answer("Выберите дату окончания:", reply_markup=date_selection_keyboard("end"))
        return
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
        await state.set_state(PassCreate.confirm)
        await show_confirmation(message, state)
        return
    if text == "👥 Всей охране":
        await state.update_data(assigned_to=None, assigned_team=Team.TEAM_SECURITY)
        await state.set_state(PassCreate.confirm)
        await show_confirmation(message, state)
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
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.message.answer("Ошибка формата")
        return
    _, emp_id_str, _ = parts
    emp_id = int(emp_id_str)
    await state.update_data(assigned_to=emp_id, assigned_team=None)
    await callback.message.delete()
    await callback.message.answer("✅ Охрана назначена.")
    await state.set_state(PassCreate.confirm)
    await show_confirmation(callback.message, state)
    await callback.answer()

async def show_confirmation(message: Message, state: FSMContext):
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
        f"Квартира: {data.get('apartment') or '—'}\n"
        f"Цель: {data.get('purpose') or '—'}\n"
        f"Начало: {data.get('start_date').strftime('%d.%m.%Y') if data.get('start_date') else '—'}\n"
        f"Окончание: {data.get('end_date').strftime('%d.%m.%Y') if data.get('end_date') else '—'}\n"
        f"Исполнитель: {executor_text}\n"
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
            apartment=data.get("apartment"),
            purpose=data.get("purpose"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            comment="",
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

# ========== Активные пропуска (все) ==========
@router.message(F.text == "📋 Активные пропуски")
async def list_active_passes(message: Message, state: FSMContext, page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE, UserRole.SECURITY):
        await message.answer("У вас нет прав для просмотра пропусков.")
        return
    await state.update_data(pass_list_type='active', pass_page=page)
    limit = 10
    all_passes = await get_passes(status="active", limit=1000, offset=0)
    total = len(all_passes)
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    start = (page - 1) * limit
    passes_page = all_passes[start:start+limit]

    if not passes_page:
        await message.answer("Нет активных пропусков.")
        return

    text = f"📋 Активные пропуски (стр. {page}/{total_pages}):\n\n"
    for p in passes_page:
        status_emoji = "🟢" if p.status == "active" else "🔵" if p.status == "used" else "🔴"
        label = f"{status_emoji} #{p.id} "
        if p.type == "guest":
            label += f"Гость: {p.guest_name or '—'}"
        else:
            label += f"Авто: {p.car_number or '—'}"
        if p.apartment:
            label += f" | кв.{p.apartment}"
        label += f" | {p.purpose or '—'}"
        text += f"{label}\n"

    sent = await message.answer(text, reply_markup=pass_list_keyboard(passes_page, page, total_pages))
    await state.update_data(pass_message_id=sent.message_id, pass_chat_id=sent.chat.id)

# ========== История пропусков ==========
@router.message(F.text == "📜 История пропусков")
async def list_history(message: Message, state: FSMContext, page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE, UserRole.SECURITY):
        await message.answer("У вас нет прав для просмотра истории пропусков.")
        return
    await state.update_data(pass_list_type='history', pass_page=page)
    limit = 10
    all_passes = await get_passes(status=['used', 'expired', 'completed'], limit=1000, offset=0)
    total = len(all_passes)
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    start = (page - 1) * limit
    passes_page = all_passes[start:start+limit]

    if not passes_page:
        await message.answer("История пуста.")
        return

    text = f"📜 История пропусков (стр. {page}/{total_pages}):\n\n"
    for p in passes_page:
        status_emoji = "🔵" if p.status == "used" else "🔴" if p.status == "expired" else "✅" if p.status == "completed" else "⚪"
        label = f"{status_emoji} #{p.id} "
        if p.type == "guest":
            label += f"Гость: {p.guest_name or '—'}"
        else:
            label += f"Авто: {p.car_number or '—'}"
        if p.apartment:
            label += f" | кв.{p.apartment}"
        label += f" | {p.purpose or '—'}"
        text += f"{label}\n"

    sent = await message.answer(text, reply_markup=pass_list_keyboard(passes_page, page, total_pages))
    await state.update_data(pass_message_id=sent.message_id, pass_chat_id=sent.chat.id)

# ========== Поиск по пропускам ==========
@router.message(F.text == "🔍 Поиск по пропускам")
async def start_search_pass(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE, UserRole.SECURITY):
        await message.answer("У вас нет прав для поиска пропусков.")
        return
    await state.set_state(PassSearch.query)
    await message.answer("Введите текст для поиска (имя гостя, номер авто, квартира, ID):")

@router.message(StateFilter(PassSearch.query))
async def process_search_pass(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE, UserRole.SECURITY):
        await message.answer("У вас нет прав для поиска пропусков.")
        await state.clear()
        return
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
    buttons = []
    for p in passes:
        status_emoji = "🟢" if p.status == "active" else "🔵" if p.status == "used" else "🔴" if p.status == "expired" else "✅" if p.status == "completed" else "⚪"
        label = f"{status_emoji} #{p.id} "
        if p.type == "guest":
            label += f"Гость: {p.guest_name or '—'}"
        else:
            label += f"Авто: {p.car_number or '—'}"
        if p.apartment:
            label += f" | кв.{p.apartment}"
        label += f" | {p.purpose or '—'}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"pass:{p.id}")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=kb)
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
        f"Квартира: {p.apartment or '—'}\n"
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
        action = entry.get("action", "—")
        user_name = entry.get("user", "Система")
        created_at = entry.get("created_at", datetime.utcnow())
        text += f"🕒 {created_at.strftime('%d.%m.%Y %H:%M')} – {user_name}: {action}\n"
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
async def paginate_passes(callback: CallbackQuery, state: FSMContext, bot):
    page = int(callback.data.split(":")[1])
    if page < 1:
        page = 1
    data = await state.get_data()
    list_type = data.get('pass_list_type', 'active')
    message_id = data.get('pass_message_id')
    chat_id = data.get('pass_chat_id')
    if not message_id or not chat_id:
        message_id = callback.message.message_id
        chat_id = callback.message.chat.id

    limit = 10
    if list_type == 'active':
        all_items = await get_passes(status="active", limit=1000, offset=0)
        title = "📋 Активные пропуски"
    else:
        all_items = await get_passes(status=['used', 'expired', 'completed'], limit=1000, offset=0)
        title = "📜 История пропусков"

    total = len(all_items)
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    start = (page - 1) * limit
    items_page = all_items[start:start+limit]

    if not items_page:
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=f"{title}\n\nНет записей.")
        await callback.answer()
        return

    text = f"{title} (стр. {page}/{total_pages}):\n\n"
    for p in items_page:
        status_emoji = "🟢" if p.status == "active" else "🔵" if p.status == "used" else "🔴" if p.status == "expired" else "✅" if p.status == "completed" else "⚪"
        label = f"{status_emoji} #{p.id} "
        if p.type == "guest":
            label += f"Гость: {p.guest_name or '—'}"
        else:
            label += f"Авто: {p.car_number or '—'}"
        if p.apartment:
            label += f" | кв.{p.apartment}"
        label += f" | {p.purpose or '—'}"
        text += f"{label}\n"

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=pass_list_keyboard(items_page, page, total_pages)
    )
    await callback.answer()

@router.callback_query(F.data == "pass_back")
async def back_to_pass_list(callback: CallbackQuery, state: FSMContext):
    employee = await get_employee(callback.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE, UserRole.SECURITY):
        await callback.answer("У вас нет прав для возврата к списку пропусков.", show_alert=True)
        return
    await state.update_data(pass_list_type='active', pass_page=1)
    await callback.message.delete()
    await list_active_passes(callback.message, state, 1)
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
    if employee:
        await message.answer("Главное меню:", reply_markup=main_menu_keyboard(employee.role))
    else:
        await message.answer("Возврат...")

@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("Действие отменено")
    employee = await get_employee(callback.from_user.id)
    if employee:
        await callback.message.answer("🚗 Меню пропусков:", reply_markup=pass_main_menu_keyboard())

# ========== Комментарии к пропускам ==========
@router.callback_query(F.data.startswith("pass_comment_menu:"))
async def pass_comment_menu(callback: CallbackQuery):
    pass_id = int(callback.data.split(":")[1])
    await callback.message.delete()
    await callback.message.answer(
        "💬 Меню комментариев:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Посмотреть комментарии", callback_data=f"pass_comment_list:{pass_id}")],
            [InlineKeyboardButton(text="✏️ Добавить комментарий", callback_data=f"pass_comment_add:{pass_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"pass_comment_back:{pass_id}")],
        ])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("pass_comment_list:"))
async def pass_comment_list(callback: CallbackQuery):
    pass_id = int(callback.data.split(":")[1])
    from app.services.passes.service import get_pass
    p = await get_pass(pass_id)
    if not p:
        await callback.answer("Не найден", show_alert=True)
        return
    comments = p.comments or []
    if not comments:
        text = "💬 Комментариев пока нет."
    else:
        text = f"💬 <b>Комментарии к пропуску #{pass_id}</b>\n\n"
        for c in comments[:10]:
            user_name = c.get("user_name", "—")
            created_at = c.get("created_at", "")
            text += f"👤 {user_name} | {created_at}\n"
            text += f"{c.get('text', '')}\n\n"
    await callback.message.delete()
    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data=f"pass_comment_menu:{pass_id}")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("pass_comment_add:"))
async def pass_comment_add(callback: CallbackQuery, state: FSMContext):
    pass_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    await state.set_state(PassCommentState.waiting_for_comment)
    await state.update_data(pass_id=pass_id)
    await callback.message.delete()
    await callback.message.answer("✍️ Введите текст комментария:")
    await callback.answer()

class PassCommentState(StatesGroup):
    waiting_for_comment = State()

@router.message(StateFilter(PassCommentState.waiting_for_comment), F.text)
async def pass_comment_process(message: Message, state: FSMContext):
    data = await state.get_data()
    pass_id = data.get("pass_id")
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка")
        await state.clear()
        return
    from app.services.passes.service import add_pass_comment
    success = await add_pass_comment(pass_id, employee.id, message.text)
    if success:
        await message.answer("✅ Комментарий добавлен.")
    else:
        await message.answer("❌ Ошибка.")
    await state.clear()
    await message.answer(
        "💬 Меню комментариев:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Посмотреть комментарии", callback_data=f"pass_comment_list:{pass_id}")],
            [InlineKeyboardButton(text="✏️ Добавить комментарий", callback_data=f"pass_comment_add:{pass_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"pass_comment_back:{pass_id}")],
        ])
    )

@router.callback_query(F.data.startswith("pass_comment_back:"))
async def pass_comment_back(callback: CallbackQuery):
    pass_id = int(callback.data.split(":")[1])
    await callback.message.delete()
    await show_pass_card(callback)
    await callback.answer()
