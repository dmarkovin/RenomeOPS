from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter

from app.services.employees.service import get_employee, get_employee_by_id
from app.services.services.service import get_all_services, get_service, create_service_order, get_user_orders
from app.services.tasks.service import get_available_employees, get_teams_with_members
from app.database.models import UserRole, Team
from app.keyboards.services import service_catalog_keyboard
from app.keyboards.object_navigation import (
    building_keyboard, parking_floor_keyboard, parking_spot_keyboard,
    cellar_keyboard, apartment_keyboard, entrance_keyboard, floor_keyboard
)
from app.keyboards.assign import (
    employee_selection_keyboard,
    team_selection_keyboard,
    service_team_selection_keyboard,
    service_employee_selection_keyboard
)
from app.keyboards.main_menu import main_menu_keyboard
from app.utils.object_navigation import get_entrances, get_floors, get_apartments, get_parking_spots, get_cellars
from app.services.notification_service import notify_user, notify_admins, notify_team
from app.permissions import has_permission, Permission

router = Router()

class ServiceOrderState(StatesGroup):
    select_service = State()
    select_object = State()
    select_applicant_type = State()
    enter_applicant_name = State()
    enter_applicant_phone = State()
    select_executor_type = State()
    select_team = State()
    select_employee = State()
    comment = State()
    photo = State()
    confirm = State()

@router.message(F.text == "💳 Платные услуги")
async def show_service_catalog(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee or not has_permission(employee, Permission.SERVICE_ORDER):
        await message.answer("У вас нет прав для заказа услуг.")
        return
    await state.clear()
    services = await get_all_services(active_only=True)
    if not services:
        await message.answer("Услуг пока нет.")
        return
    await state.set_state(ServiceOrderState.select_service)
    await message.answer(
        "💰 Каталог платных услуг:\nВыберите услугу:",
        reply_markup=service_catalog_keyboard(services)
    )

@router.callback_query(StateFilter(ServiceOrderState.select_service), F.data.startswith("service_order:"))
async def select_service(callback: CallbackQuery, state: FSMContext):
    employee = await get_employee(callback.from_user.id)
    if not employee or not has_permission(employee, Permission.SERVICE_ORDER):
        await callback.answer("У вас нет прав", show_alert=True)
        return
    service_id = int(callback.data.split(":")[1])
    service = await get_service(service_id)
    if not service:
        await callback.answer("Услуга не найдена", show_alert=True)
        return
    await state.update_data(service_id=service_id, service_name=service.name)
    await state.set_state(ServiceOrderState.select_object)
    await callback.message.edit_text(
        f"📝 Заказ услуги: {service.name}\n"
        f"Цена: {service.price} руб.\n\n"
        "Выберите локацию (квартиру, паркинг или келлер):",
        reply_markup=building_keyboard()
    )
    await callback.answer()

@router.callback_query(StateFilter(ServiceOrderState.select_object), F.data.startswith("obj_building:"))
async def process_building(callback: CallbackQuery, state: FSMContext):
    building_id = int(callback.data.split(":")[1])
    await state.update_data(building=building_id)
    entrances = get_entrances(building_id)
    await state.update_data(object_type="apartment")
    await callback.message.edit_text(
        f"🏢 Выберите подъезд для корпуса {building_id}:",
        reply_markup=entrance_keyboard(building_id, entrances)
    )
    await callback.answer()

@router.callback_query(StateFilter(ServiceOrderState.select_object), F.data.startswith("obj_entrance:"))
async def process_entrance(callback: CallbackQuery, state: FSMContext):
    _, building_id_str, entrance_str = callback.data.split(":")
    building_id = int(building_id_str)
    entrance = int(entrance_str)
    await state.update_data(entrance=entrance)
    floors = get_floors(building_id, entrance)
    await callback.message.edit_text(
        f"🏗 Выберите этаж (подъезд {entrance}):",
        reply_markup=floor_keyboard(building_id, entrance, floors)
    )
    await callback.answer()

@router.callback_query(StateFilter(ServiceOrderState.select_object), F.data.startswith("obj_floor:"))
async def process_floor(callback: CallbackQuery, state: FSMContext):
    _, building_id_str, entrance_str, floor_str = callback.data.split(":")
    building_id = int(building_id_str)
    entrance = int(entrance_str)
    floor = int(floor_str)
    await state.update_data(floor=floor)
    apartments = get_apartments(building_id, entrance, floor)
    if not apartments:
        await callback.message.edit_text("На этом этаже нет квартир. Выберите другой этаж.")
        return
    await callback.message.edit_text(
        f"🏠 Выберите квартиру на этаже {floor}:",
        reply_markup=apartment_keyboard(building_id, entrance, floor, apartments)
    )
    await callback.answer()

@router.callback_query(StateFilter(ServiceOrderState.select_object), F.data.startswith("obj_apartment:"))
async def handle_apartment_selection(callback: CallbackQuery, state: FSMContext):
    _, building_str, entrance_str, floor_str, apt_str = callback.data.split(":")
    building = int(building_str)
    entrance = int(entrance_str)
    floor = int(floor_str)
    apartment = int(apt_str)
    await state.update_data(object_data={
        "building": building,
        "entrance": entrance,
        "floor": floor,
        "apartment": apartment,
        "type": "apartment"
    })
    await callback.message.edit_text(f"✅ Выбрана квартира {apartment} (корпус {building})")
    await state.set_state(ServiceOrderState.select_applicant_type)
    await callback.message.answer(
        "Кто является заявителем?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="👤 Жилец")],
                [KeyboardButton(text="👤 Сотрудник")],
            ],
            resize_keyboard=True
        )
    )
    await callback.answer()

@router.callback_query(StateFilter(ServiceOrderState.select_object), F.data == "obj_parking")
async def handle_parking_start(callback: CallbackQuery, state: FSMContext):
    await state.update_data(object_type="parking")
    await callback.message.edit_text(
        "🚗 Выберите уровень паркинга:",
        reply_markup=parking_floor_keyboard(2, [-1, -2])
    )
    await callback.answer()

@router.callback_query(StateFilter(ServiceOrderState.select_object), F.data.startswith("obj_parking_floor:"))
async def handle_parking_floor(callback: CallbackQuery, state: FSMContext):
    _, building_str, floor_str = callback.data.split(":")
    building = int(building_str)
    floor = int(floor_str)
    await state.update_data(parking_floor=floor)
    spots = get_parking_spots(building, floor)
    await callback.message.edit_text(
        f"🚗 Выберите машиноместо на этаже {floor}:",
        reply_markup=parking_spot_keyboard(building, floor, spots)
    )
    await callback.answer()

@router.callback_query(StateFilter(ServiceOrderState.select_object), F.data.startswith("obj_parking_spot:"))
async def handle_parking_spot(callback: CallbackQuery, state: FSMContext):
    _, building_str, floor_str, spot_str = callback.data.split(":")
    building = int(building_str)
    floor = int(floor_str)
    spot = int(spot_str)
    await state.update_data(object_data={
        "building": building,
        "parking_floor": floor,
        "parking_spot": spot,
        "type": "parking"
    })
    await callback.message.edit_text(f"✅ Выбрано машиноместо {spot} (этаж {floor})")
    await state.set_state(ServiceOrderState.select_applicant_type)
    await callback.message.answer(
        "Кто является заявителем?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="👤 Жилец")],
                [KeyboardButton(text="👤 Сотрудник")],
            ],
            resize_keyboard=True
        )
    )
    await callback.answer()

@router.callback_query(StateFilter(ServiceOrderState.select_object), F.data.startswith("obj_cellar:"))
async def handle_cellar_selection(callback: CallbackQuery, state: FSMContext):
    _, building_str, cellar_str = callback.data.split(":")
    building = int(building_str)
    cellar = int(cellar_str)
    await state.update_data(object_data={
        "building": building,
        "cellar": cellar,
        "type": "cellar"
    })
    await callback.message.edit_text(f"✅ Выбран келлер {cellar} (корпус {building})")
    await state.set_state(ServiceOrderState.select_applicant_type)
    await callback.message.answer(
        "Кто является заявителем?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="👤 Жилец")],
                [KeyboardButton(text="👤 Сотрудник")],
            ],
            resize_keyboard=True
        )
    )
    await callback.answer()

@router.message(ServiceOrderState.select_applicant_type, F.text.in_(["👤 Жилец", "👤 Сотрудник"]))
async def process_applicant_type(message: Message, state: FSMContext):
    app_type = "resident" if message.text == "👤 Жилец" else "employee"
    await state.update_data(applicant_type=app_type)
    await state.set_state(ServiceOrderState.enter_applicant_name)
    await message.answer("Введите ФИО заявителя:", reply_markup=ReplyKeyboardRemove())

@router.message(ServiceOrderState.enter_applicant_name)
async def process_applicant_name(message: Message, state: FSMContext):
    await state.update_data(applicant_name=message.text.strip())
    await state.set_state(ServiceOrderState.enter_applicant_phone)
    await message.answer("Введите телефон для связи (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(ServiceOrderState.enter_applicant_phone)
async def process_applicant_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    await state.update_data(applicant_phone=phone if phone != "-" else "")
    await state.set_state(ServiceOrderState.select_executor_type)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Команда")],
            [KeyboardButton(text="👤 Сотрудник")],
            [KeyboardButton(text="⏭ Пропустить")],
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите способ назначения исполнителя:", reply_markup=kb)

@router.message(ServiceOrderState.select_executor_type, F.text.in_(["👥 Команда", "👤 Сотрудник", "⏭ Пропустить"]))
async def process_executor_type(message: Message, state: FSMContext):
    text = message.text
    if text == "⏭ Пропустить":
        await state.update_data(assigned_to=None, assigned_team=None)
        await state.set_state(ServiceOrderState.comment)
        await message.answer("Введите комментарий (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())
        return
    if text == "👥 Команда":
        teams = await get_teams_with_members()
        if not teams:
            await message.answer("Нет доступных команд.")
            return
        await state.set_state(ServiceOrderState.select_team)
        await message.answer("Выберите команду:", reply_markup=service_team_selection_keyboard(teams))
        return
    if text == "👤 Сотрудник":
        employees = await get_available_employees()
        if not employees:
            await message.answer("Нет доступных сотрудников.")
            return
        await state.set_state(ServiceOrderState.select_employee)
        await message.answer("Выберите сотрудника:", reply_markup=service_employee_selection_keyboard(employees))
        return

@router.callback_query(StateFilter(ServiceOrderState.select_team), F.data.startswith("service_team:"))
async def process_service_team(callback: CallbackQuery, state: FSMContext):
    employee = await get_employee(callback.from_user.id)
    if not employee or not has_permission(employee, Permission.SERVICE_ORDER):
        await callback.answer("Нет прав", show_alert=True)
        return
    team_str = callback.data.split(":")[1]
    team = Team(team_str)
    await state.update_data(assigned_team=team, assigned_to=None)
    await callback.message.edit_text(f"✅ Выбрана команда {team.value}")
    await state.set_state(ServiceOrderState.comment)
    await callback.message.answer("Введите комментарий (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())
    await callback.answer()

@router.callback_query(StateFilter(ServiceOrderState.select_employee), F.data.startswith("service_emp:"))
async def process_service_employee(callback: CallbackQuery, state: FSMContext):
    employee = await get_employee(callback.from_user.id)
    if not employee or not has_permission(employee, Permission.SERVICE_ORDER):
        await callback.answer("Нет прав", show_alert=True)
        return
    emp_id = int(callback.data.split(":")[1])
    await state.update_data(assigned_to=emp_id, assigned_team=None)
    await callback.message.edit_text("✅ Выбран сотрудник")
    await state.set_state(ServiceOrderState.comment)
    await callback.message.answer("Введите комментарий (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())
    await callback.answer()

@router.callback_query(F.data == "service_cancel")
async def service_cancel(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ServiceOrderState.select_executor_type)
    await callback.message.delete()
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Команда")],
            [KeyboardButton(text="👤 Сотрудник")],
            [KeyboardButton(text="⏭ Пропустить")],
        ],
        resize_keyboard=True
    )
    await callback.message.answer("Выберите способ назначения исполнителя:", reply_markup=kb)
    await callback.answer()

@router.message(ServiceOrderState.comment)
async def process_comment(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(comment=text if text != "-" else "")
    await state.set_state(ServiceOrderState.photo)
    await message.answer("🖼 Пришлите фото (опционально) или нажмите **Готово**:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Готово")]],
        resize_keyboard=True
    ))

@router.message(ServiceOrderState.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Добавлено фото ({len(photos)})")

@router.message(ServiceOrderState.photo, F.text == "✅ Готово")
async def finish_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    assigned_to = data.get('assigned_to')
    assigned_team = data.get('assigned_team')
    if assigned_to:
        executor = await get_employee_by_id(assigned_to)
        executor_text = executor.full_name if executor else "назначен"
    elif assigned_team:
        executor_text = f"команда {assigned_team.value}"
    else:
        executor_text = "не назначен (будет назначена на консьержей)"
    text = (
        f"📝 Проверьте данные заказа:\n\n"
        f"Услуга: {data.get('service_name')}\n"
        f"Локация: {data.get('object_data')}\n"
        f"Заявитель: {data.get('applicant_name')} ({data.get('applicant_type')})\n"
        f"Телефон: {data.get('applicant_phone') or '—'}\n"
        f"Исполнитель: {executor_text}\n"
        f"Комментарий: {data.get('comment') or '—'}\n"
        f"Фото: {len(data.get('photos', []))} шт.\n\n"
        f"Подтвердить создание?"
    )
    await state.set_state(ServiceOrderState.confirm)
    await message.answer(text, reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Да, создать")], [KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))

@router.message(ServiceOrderState.confirm, F.text == "✅ Да, создать")
async def confirm_create_order(message: Message, state: FSMContext):
    data = await state.get_data()
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка.")
        await state.clear()
        return
    if not has_permission(employee, Permission.SERVICE_ORDER):
        await message.answer("У вас нет прав на создание заказа.")
        await state.clear()
        return
    try:
        order = await create_service_order(
            service_id=data.get("service_id"),
            user_id=employee.id,
            object_data=data.get("object_data"),
            applicant_type=data.get("applicant_type"),
            applicant_name=data.get("applicant_name"),
            applicant_phone=data.get("applicant_phone"),
            assigned_to=data.get("assigned_to"),
            assigned_team=data.get("assigned_team"),
            comment=data.get("comment"),
            photo_ids=data.get("photos", [])
        )
        await state.clear()
        if data.get("assigned_to"):
            assignee = await get_employee_by_id(data["assigned_to"])
            if assignee and assignee.telegram_id:
                await notify_user(assignee.telegram_id, f"📢 Вам назначена платная услуга #{order.id}.")
        elif data.get("assigned_team"):
            await notify_team(data["assigned_team"], f"📢 Новая платная услуга #{order.id} назначена на вашу команду.")
        await notify_admins(f"📢 Создан новый заказ услуги #{order.id} от {employee.full_name}.")
        await message.answer(f"✅ Заказ #{order.id} создан!", reply_markup=main_menu_keyboard(employee.role))
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", parse_mode=None)
        await state.clear()

@router.message(ServiceOrderState.confirm, F.text == "❌ Отмена")
async def cancel_order(message: Message, state: FSMContext):
    await state.clear()
    employee = await get_employee(message.from_user.id)
    await message.answer("Отменено", reply_markup=main_menu_keyboard(employee.role) if employee else None)

@router.message(F.text == "📋 Мои заказы")
async def show_user_orders(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    if not has_permission(employee, Permission.SERVICE_ORDER):
        await message.answer("У вас нет прав на просмотр заказов.")
        return
    orders = await get_user_orders(employee.id)
    if not orders:
        await message.answer("У вас нет заказов.")
        return
    text = "📋 Ваши заказы:\n\n"
    for o in orders:
        service = await get_service(o.service_id)
        service_name = service.name if service else "Неизвестно"
        text += f"ID: {o.id} | Услуга: {service_name} | Статус: {o.status} | {o.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    await message.answer(text)

# ========== ОБРАБОТЧИК КНОПКИ "НАЗАД" ==========
@router.callback_query(F.data == "service_back")
async def service_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    await callback.message.delete()
    await callback.message.answer(
        "Главное меню:",
        reply_markup=main_menu_keyboard(employee.role)
    )
    await callback.answer()
