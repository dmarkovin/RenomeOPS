from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter
from datetime import datetime, timedelta

from app.services.employees.service import get_employee, get_employee_by_id
from app.services.passes.service import (
    create_pass, get_pass, get_passes,
    check_in, check_out, update_pass_status
)
from app.services.tasks.service import get_available_employees
from app.database.models import UserRole, Team
from app.keyboards.passes import (
    pass_list_keyboard, pass_action_keyboard, pass_main_menu_keyboard
)
from app.keyboards.assign import employee_selection_keyboard
from app.keyboards.date_picker import date_selection_keyboard
from app.keyboards.main_menu import main_menu_keyboard
from app.services.notification_service import notify_user, notify_team, notify_concierges, notify_security

router = Router()

class PassCreate(StatesGroup):
    type = State()
    guest_name = State()
    car_number = State()
    purpose = State()
    start_date = State()
    end_date = State()
    assign_employee = State()
    comment = State()
    confirm = State()
    select_start_date = State()
    select_end_date = State()

@router.message(F.text == "🚗 Пропуска")
async def passes_menu(message: Message, page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE, UserRole.SECURITY):
        await message.answer("У вас нет прав.")
        return

    limit = 10
    offset = (page - 1) * limit
    if employee.role == UserRole.SECURITY:
        passes = await get_passes(assigned_to=employee.id, limit=limit, offset=offset)
    else:
        passes = await get_passes(limit=limit, offset=offset)
    total = len(passes)
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    if not passes:
        await message.answer("Нет пропусков.", reply_markup=pass_main_menu_keyboard())
        return

    text = "📋 Список пропусков:\n\n"
    for p in passes:
        status_emoji = "🟢" if p.status == "active" else "🔵" if p.status == "used" else "🔴"
        label = p.guest_name or p.car_number or "—"
        text += f"{status_emoji} #{p.id} {label} ({p.type}) – {p.status}\n"
    await message.answer(text, reply_markup=pass_list_keyboard(passes, page, total_pages))

@router.message(F.text == "➕ Новый пропуск")
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
        await message.answer("Введите имя гостя:")
    else:
        await message.answer("Введите номер автомобиля:")

@router.message(PassCreate.guest_name)
async def process_guest_name(message: Message, state: FSMContext):
    await state.update_data(guest_name=message.text.strip())
    await state.set_state(PassCreate.purpose)
    await message.answer("Введите цель визита (или '-' для пропуска):")

@router.message(PassCreate.car_number)
async def process_car_number(message: Message, state: FSMContext):
    await state.update_data(car_number=message.text.strip())
    await state.set_state(PassCreate.purpose)
    await message.answer("Введите цель визита (или '-' для пропуска):")

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
    employees = await get_available_employees(role=UserRole.SECURITY)
    if employees:
        await state.set_state(PassCreate.assign_employee)
        await callback.message.edit_text("Выберите сотрудника охраны:", reply_markup=employee_selection_keyboard(employees, "pass_assign", 0))
    else:
        await state.update_data(assigned_to=None)
        await state.set_state(PassCreate.comment)
        await callback.message.edit_text("Нет доступных сотрудников охраны. Пропуск будет создан без назначения.")
        await callback.message.answer("Введите комментарий (или '-' для пропуска):")
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
    employees = await get_available_employees(role=UserRole.SECURITY)
    if employees:
        await state.set_state(PassCreate.assign_employee)
        await message.answer("Выберите сотрудника охраны:", reply_markup=employee_selection_keyboard(employees, "pass_assign", 0))
    else:
        await state.update_data(assigned_to=None)
        await state.set_state(PassCreate.comment)
        await message.answer("Нет доступных сотрудников охраны. Пропуск будет создан без назначения.")
        await message.answer("Введите комментарий (или '-' для пропуска):")

@router.callback_query(F.data.startswith("pass_assign:"))
async def process_assign_employee(callback: CallbackQuery, state: FSMContext):
    _, emp_id_str, _ = callback.data.split(":")
    emp_id = int(emp_id_str)
    await state.update_data(assigned_to=emp_id)
    await callback.message.edit_text("✅ Охрана назначена.")
    await state.set_state(PassCreate.comment)
    await callback.message.answer("Введите комментарий (или '-' для пропуска):")
    await callback.answer()

@router.message(PassCreate.comment)
async def process_comment(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(comment=text if text != "-" else "")
    # Переходим к подтверждению
    await state.set_state(PassCreate.confirm)
    data = await state.get_data()
    text = (
        f"📝 Проверьте данные пропуска:\n\n"
        f"Тип: {data.get('type')}\n"
        f"Гость: {data.get('guest_name') or '—'}\n"
        f"Авто: {data.get('car_number') or '—'}\n"
        f"Цель: {data.get('purpose') or '—'}\n"
        f"Начало: {data.get('start_date').strftime('%d.%m.%Y') if data.get('start_date') else '—'}\n"
        f"Окончание: {data.get('end_date').strftime('%d.%m.%Y') if data.get('end_date') else '—'}\n"
        f"Охрана: {data.get('assigned_to') or 'не назначена'}\n"
        f"Комментарий: {data.get('comment') or '—'}\n\n"
        f"Подтвердить создание?"
    )
    await message.answer(text, reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="✅ Да, создать")], [types.KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))

@router.message(PassCreate.confirm, F.text == "✅ Да, создать")
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
            photo_ids=[],  # больше не используем фото
            created_by=employee.id,
            assigned_to=data.get("assigned_to")
        )
        await state.clear()
        if p.assigned_to:
            guard = await get_employee_by_id(p.assigned_to)
            if guard and guard.telegram_id:
                await notify_user(guard.telegram_id, f"🪪 Вам назначен пропуск #{p.id}.")
        await notify_concierges(f"🪪 Создан новый пропуск #{p.id} для {p.guest_name or p.car_number}.")
        await notify_security(f"🪪 Создан новый пропуск #{p.id} для {p.guest_name or p.car_number}.")
        await message.answer(f"✅ Пропуск #{p.id} создан!", reply_markup=pass_main_menu_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", parse_mode=None)
        await state.clear()

@router.message(PassCreate.confirm, F.text == "❌ Отмена")
async def cancel_create_pass(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено", reply_markup=pass_main_menu_keyboard())

# Карточка пропуска
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
    await callback.message.edit_text(text, reply_markup=pass_action_keyboard(p.id, p.status, user_role))
    await callback.answer()

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

@router.callback_query(F.data.startswith("pass_page:"))
async def paginate_passes(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    await passes_menu(callback.message, page)
    await callback.answer()

@router.callback_query(F.data == "pass_back")
async def back_to_pass_menu(callback: CallbackQuery):
    await callback.message.delete()
    employee = await get_employee(callback.from_user.id)
    await callback.message.answer("Меню пропусков", reply_markup=pass_main_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("Действие отменено")
    employee = await get_employee(callback.from_user.id)
    if employee:
        await callback.message.answer("Главное меню", reply_markup=main_menu_keyboard(employee.role))

@router.callback_query(F.data.startswith("pass_history:"))
async def pass_history(callback: CallbackQuery):
    pass_id = int(callback.data.split(":")[1])
    from app.services.passes.service import get_pass_history
    history = await get_pass_history(pass_id)
    if not history:
        await callback.answer("История пуста", show_alert=True)
        return
    text = f"📜 История пропуска #{pass_id}:\n\n"
    for h in history[:10]:
        action_emoji = {
            "created": "🟢",
            "checkin": "✅",
            "checkout": "🚗",
            "status_used": "🔵",
            "status_completed": "✅",
            "status_expired": "🔴"
        }.get(h.action, "📌")
        user_name = h.user.full_name if h.user else "Система"
        text += f"{action_emoji} {h.created_at.strftime('%d.%m.%Y %H:%M')} – {user_name}: {h.comment or h.action}\n"
    if len(history) > 10:
        text += "\n... и ещё записи."
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()
