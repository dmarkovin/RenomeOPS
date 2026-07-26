from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter

from app.services.employees.service import get_employee
from app.services.tasks.service import create_task
from app.services.notification_service import notify_admins
from app.database.models import UserRole
from app.keyboards.main_menu import main_menu_keyboard
from app.keyboards.object_navigation import (
    building_keyboard, entrance_keyboard, floor_keyboard,
    apartment_keyboard, parking_floor_keyboard, parking_spot_keyboard,
    cellar_keyboard, location_type_keyboard, parking_type_keyboard
)
from app.utils.object_navigation import (
    get_entrances, get_floors, get_apartments,
    get_parking_floors, get_parking_spots, get_cellars
)
from app.utils.location_types import get_location_type_name
from app.keyboards.assign import assign_type_keyboard
from app.keyboards.priority import priority_keyboard, get_priority_name

router = Router()

class TaskCreate(StatesGroup):
    select_building = State()
    select_entrance = State()
    select_floor = State()
    select_location_type = State()
    select_apartment = State()
    select_parking_floor = State()
    select_parking_spot = State()
    select_cellar = State()
    enter_title = State()
    enter_description = State()
    enter_applicant_type = State()
    enter_applicant_name = State()
    enter_applicant_phone = State()
    enter_priority = State()
    enter_photo = State()
    confirm = State()

@router.message(F.text == "➕ Создать заявку")
async def start_create_task(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE):
        await message.answer("У вас нет прав для создания заявок.")
        return
    await state.clear()
    await state.set_state(TaskCreate.select_building)
    await message.answer("📍 Выберите место:", reply_markup=building_keyboard())

# ---------- Навигация ----------
@router.callback_query(StateFilter(TaskCreate.select_building), F.data.startswith("obj_building:"))
async def process_building(callback: CallbackQuery, state: FSMContext):
    building_id = int(callback.data.split(":")[1])
    await state.update_data(building=building_id)
    entrances = get_entrances(building_id)
    await state.set_state(TaskCreate.select_entrance)
    await callback.message.edit_text(
        f"🏢 Выберите подъезд для корпуса {building_id}:",
        reply_markup=entrance_keyboard(building_id, entrances)
    )
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_building), F.data == "obj_parking")
async def process_parking(callback: CallbackQuery, state: FSMContext):
    await state.update_data(building=2, location_type="parking")
    floors = [-1, -2]
    await state.set_state(TaskCreate.select_parking_floor)
    await callback.message.edit_text(
        "🚗 Выберите уровень паркинга:",
        reply_markup=parking_floor_keyboard(2, floors)
    )
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_entrance), F.data.startswith("obj_entrance:"))
async def process_entrance(callback: CallbackQuery, state: FSMContext):
    _, building_id_str, entrance_str = callback.data.split(":")
    building_id = int(building_id_str)
    entrance = int(entrance_str)
    await state.update_data(entrance=entrance)
    floors = get_floors(building_id, entrance)
    await state.set_state(TaskCreate.select_floor)
    await callback.message.edit_text(
        f"🏗 Выберите этаж (подъезд {entrance}):",
        reply_markup=floor_keyboard(building_id, entrance, floors)
    )
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_floor), F.data.startswith("obj_floor:"))
async def process_floor(callback: CallbackQuery, state: FSMContext):
    _, building_id_str, entrance_str, floor_str = callback.data.split(":")
    building_id = int(building_id_str)
    entrance = int(entrance_str)
    floor = int(floor_str)
    await state.update_data(floor=floor)
    await state.set_state(TaskCreate.select_location_type)
    await callback.message.edit_text(
        "🏷️ Выберите, к чему относится проблема:",
        reply_markup=location_type_keyboard()
    )
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_location_type), F.data.startswith("loc_type:"))
async def process_location_type(callback: CallbackQuery, state: FSMContext):
    loc_type = callback.data.split(":")[1]
    await state.update_data(location_type=loc_type)
    if loc_type == "apartment":
        data = await state.get_data()
        building = data.get("building")
        entrance = data.get("entrance")
        floor = data.get("floor")
        apartments = get_apartments(building, entrance, floor)
        await state.set_state(TaskCreate.select_apartment)
        await callback.message.edit_text(
            f"🏠 Выберите квартиру на этаже {floor}:",
            reply_markup=apartment_keyboard(building, entrance, floor, apartments)
        )
    else:
        await callback.message.edit_text("✅ Тип локации выбран.")
        await state.set_state(TaskCreate.enter_title)
        await callback.message.answer("📝 Введите **название** заявки:")
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_apartment), F.data.startswith("obj_apartment:"))
async def process_apartment(callback: CallbackQuery, state: FSMContext):
    _, building_str, entrance_str, floor_str, apt_str = callback.data.split(":")
    apartment = int(apt_str)
    await state.update_data(apartment=apartment)
    await callback.message.edit_text(f"✅ Выбрана квартира {apartment}")
    await state.set_state(TaskCreate.enter_title)
    await callback.message.answer("📝 Введите **название** заявки:")
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_parking_floor), F.data.startswith("obj_parking_floor:"))
async def process_parking_floor(callback: CallbackQuery, state: FSMContext):
    _, building_str, floor_str = callback.data.split(":")
    building = int(building_str)
    floor = int(floor_str)
    await state.update_data(parking_level=floor)
    await callback.message.edit_text(
        "🚗 Выберите тип проблемы на паркинге:",
        reply_markup=parking_type_keyboard()
    )
    await state.set_state(TaskCreate.select_location_type)
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_location_type), F.data.startswith("parking_type:"))
async def process_parking_type(callback: CallbackQuery, state: FSMContext):
    ptype = callback.data.split(":")[1]
    await state.update_data(location_type=f"parking_{ptype}")
    data = await state.get_data()
    building = data.get("building", 2)
    if ptype == "parking_spot":
        floor = data.get("parking_level")
        spots = get_parking_spots(building, floor)
        await state.set_state(TaskCreate.select_parking_spot)
        await callback.message.edit_text(
            "🚗 Выберите машиноместо:",
            reply_markup=parking_spot_keyboard(building, floor, spots)
        )
    elif ptype == "cellar":
        cellars = get_cellars(building)
        await state.set_state(TaskCreate.select_cellar)
        await callback.message.edit_text(
            "🔐 Выберите келлер:",
            reply_markup=cellar_keyboard(building, cellars)
        )
    else:
        await callback.message.edit_text("✅ Тип проблемы выбран.")
        await state.set_state(TaskCreate.enter_title)
        await callback.message.answer("📝 Введите **название** заявки:")
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_parking_spot), F.data.startswith("obj_parking_spot:"))
async def process_parking_spot(callback: CallbackQuery, state: FSMContext):
    _, building_str, floor_str, spot_str = callback.data.split(":")
    spot = int(spot_str)
    await state.update_data(parking_spot=spot)
    await callback.message.edit_text(f"✅ Выбрано машиноместо {spot}")
    await state.set_state(TaskCreate.enter_title)
    await callback.message.answer("📝 Введите **название** заявки:")
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_cellar), F.data.startswith("obj_cellar:"))
async def process_cellar(callback: CallbackQuery, state: FSMContext):
    _, building_str, cellar_str = callback.data.split(":")
    cellar = int(cellar_str)
    await state.update_data(cellar=cellar)
    await callback.message.edit_text(f"✅ Выбран келлер {cellar}")
    await state.set_state(TaskCreate.enter_title)
    await callback.message.answer("📝 Введите **название** заявки:")
    await callback.answer()

# ---------- Название и описание ----------
@router.message(StateFilter(TaskCreate.enter_title), F.text)
async def process_title(message: Message, state: FSMContext):
    if len(message.text.strip()) < 3:
        await message.answer("Название должно быть не короче 3 символов.")
        return
    await state.update_data(title=message.text.strip())
    await state.set_state(TaskCreate.enter_description)
    await message.answer("📄 Введите **описание** (или '-' для пропуска):")

@router.message(StateFilter(TaskCreate.enter_description), F.text)
async def process_description(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(description=text if text != "-" else "")
    await state.set_state(TaskCreate.enter_applicant_type)
    # Выбор типа заявителя
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Жилец")],
            [KeyboardButton(text="👤 Сотрудник")],
        ],
        resize_keyboard=True
    )
    await message.answer("Кто является заявителем?", reply_markup=kb)

# ---------- Заявитель ----------
@router.message(StateFilter(TaskCreate.enter_applicant_type), F.text.in_(["👤 Жилец", "👤 Сотрудник"]))
async def process_applicant_type(message: Message, state: FSMContext):
    app_type = "resident" if message.text == "👤 Жилец" else "employee"
    await state.update_data(applicant_type=app_type)
    await state.set_state(TaskCreate.enter_applicant_name)
    await message.answer("Введите ФИО заявителя:", reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))

@router.message(StateFilter(TaskCreate.enter_applicant_name), F.text)
async def process_applicant_name(message: Message, state: FSMContext):
    await state.update_data(applicant_name=message.text.strip())
    await state.set_state(TaskCreate.enter_applicant_phone)
    await message.answer("Введите телефон для связи (или '-' для пропуска):")

@router.message(StateFilter(TaskCreate.enter_applicant_phone), F.text)
async def process_applicant_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    await state.update_data(applicant_phone=phone if phone != "-" else "")
    # Переходим к выбору приоритета
    await state.set_state(TaskCreate.enter_priority)
    await message.answer("Выберите приоритет заявки:", reply_markup=priority_keyboard())

# ---------- Приоритет ----------
@router.callback_query(StateFilter(TaskCreate.enter_priority), F.data.startswith("priority:"))
async def process_priority(callback: CallbackQuery, state: FSMContext):
    priority = int(callback.data.split(":")[1])
    await state.update_data(priority=priority)
    await callback.message.edit_text(f"✅ Выбран приоритет: {get_priority_name(priority)}")
    await state.set_state(TaskCreate.enter_photo)
    await callback.message.answer(
        "🖼 Пришлите фото (опционально) или нажмите **Готово**:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="✅ Готово")]],
            resize_keyboard=True
        )
    )
    await callback.answer()

# ---------- Фото ----------
@router.message(StateFilter(TaskCreate.enter_photo), F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Добавлено фото ({len(photos)})")

@router.message(StateFilter(TaskCreate.enter_photo), F.text == "✅ Готово")
async def finish_photos(message: Message, state: FSMContext):
    await state.set_state(TaskCreate.confirm)
    data = await state.get_data()
    text = (
        f"📝 **Проверьте данные заявки:**\n\n"
        f"Название: {data.get('title')}\n"
        f"Описание: {data.get('description') or '—'}\n"
        f"Корпус: {data.get('building')}\n"
        f"Подъезд: {data.get('entrance') or '—'}\n"
        f"Этаж: {data.get('floor') or '—'}\n"
        f"Квартира: {data.get('apartment') or '—'}\n"
        f"Тип локации: {get_location_type_name(data.get('location_type'))}\n"
        f"Паркинг уровень: {data.get('parking_level') or '—'}\n"
        f"Машиноместо: {data.get('parking_spot') or '—'}\n"
        f"Келлер: {data.get('cellar') or '—'}\n"
        f"Заявитель: {data.get('applicant_type') == 'resident' and 'Жилец' or 'Сотрудник'}\n"
        f"ФИО заявителя: {data.get('applicant_name') or '—'}\n"
        f"Телефон: {data.get('applicant_phone') or '—'}\n"
        f"Приоритет: {get_priority_name(data.get('priority', 3))}\n"
        f"Фото: {len(data.get('photos', []))} шт.\n\n"
        f"Подтвердить создание?"
    )
    await message.answer(
        text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="✅ Да, создать")], [KeyboardButton(text="❌ Отмена")]],
            resize_keyboard=True
        )
    )

# ---------- Подтверждение ----------
@router.message(StateFilter(TaskCreate.confirm), F.text == "✅ Да, создать")
async def confirm_create(message: Message, state: FSMContext):
    data = await state.get_data()
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка: пользователь не найден.")
        await state.clear()
        return
    try:
        task = await create_task(
            title=data.get("title"),
            description=data.get("description"),
            created_by=employee.id,
            building=data.get("building"),
            entrance=data.get("entrance"),
            floor=data.get("floor"),
            apartment=data.get("apartment"),
            location_type=data.get("location_type"),
            parking_level=data.get("parking_level"),
            parking_spot=data.get("parking_spot"),
            cellar=data.get("cellar"),
            applicant_type=data.get("applicant_type"),
            applicant_name=data.get("applicant_name"),
            applicant_phone=data.get("applicant_phone"),
            priority=data.get("priority", 3),
            photo_ids=data.get("photos", [])
        )
        await state.clear()
        await notify_admins(f"📢 Новая заявка #{task.id}: {task.title} создана сотрудником {employee.full_name}")
        await message.answer(
            f"✅ Заявка #{task.id} создана! Теперь назначьте её.",
            reply_markup=assign_type_keyboard(task.id)
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при создании: {str(e)}", parse_mode=None)
        await state.clear()
        await message.answer("Попробуйте снова.", reply_markup=main_menu_keyboard(employee.role))

@router.message(StateFilter(TaskCreate.confirm), F.text == "❌ Отмена")
async def cancel_creation(message: Message, state: FSMContext):
    await state.clear()
    employee = await get_employee(message.from_user.id)
    await message.answer(
        "❌ Создание отменено.",
        reply_markup=main_menu_keyboard(employee.role) if employee else None
    )

@router.callback_query(F.data == "obj_cancel")
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("Отменено")
    employee = await get_employee(callback.from_user.id)
    if employee:
        await callback.message.answer("Возврат в меню", reply_markup=main_menu_keyboard(employee.role))
