from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter

from app.services.employees.service import get_employee
from app.services.tasks.service import create_task
from app.services.notification_service import notify_admins_with_button, notify_team_with_button
from app.database.models import UserRole, Team
from app.keyboards.main_menu import main_menu_keyboard
from app.keyboards.object_navigation import (
    building_keyboard, entrance_keyboard, floor_keyboard,
    apartment_keyboard, parking_floor_keyboard, parking_spot_keyboard,
    cellar_keyboard
)
from app.keyboards.priority import priority_keyboard
from app.keyboards.tasks import tasks_menu_keyboard
from app.keyboards.task_actions import task_actions_keyboard
from app.utils.object_navigation import get_entrances, get_floors, get_apartments, get_parking_spots, get_cellars, get_common_area_name

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
    enter_media = State()
    confirm = State()

async def safe_delete_message(message):
    try:
        await message.delete()
    except Exception:
        pass

@router.message(F.text == "➕ Создать заявку")
async def start_create_task(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE):
        await message.answer("У вас нет прав на создание заявки.")
        return
    await state.clear()
    await state.set_state(TaskCreate.select_building)
    await message.answer(
        "🏢 Выберите объект (корпус, паркинг или келлер):",
        reply_markup=building_keyboard()
    )

# --- Обработчики выбора объекта ---
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
    await state.set_state(TaskCreate.select_parking_floor)
    await callback.message.edit_text(
        "🚗 Выберите уровень паркинга:",
        reply_markup=parking_floor_keyboard(2, [-1, -2])
    )
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_building), F.data.startswith("obj_cellar:"))
async def process_cellar_start(callback: CallbackQuery, state: FSMContext):
    building_id = int(callback.data.split(":")[1])
    await state.update_data(building=building_id)
    cellars = get_cellars(building_id)
    await state.set_state(TaskCreate.select_cellar)
    await callback.message.edit_text(
        f"🔐 Выберите келлер для корпуса {building_id}:",
        reply_markup=cellar_keyboard(building_id, cellars, 0)
    )
    await callback.answer()

# --- Выбор подъезда, этажа, квартиры ---
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
    apartments = get_apartments(building_id, entrance, floor)
    if not apartments:
        await callback.message.edit_text("На этом этаже нет квартир. Выберите другой этаж.")
        return
    await state.set_state(TaskCreate.select_apartment)
    await callback.message.edit_text(
        f"🏠 Выберите на этаже {floor}:",
        reply_markup=apartment_keyboard(building_id, entrance, floor, apartments)
    )
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_apartment), F.data.startswith("obj_apartment:"))
async def process_apartment(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    building = int(parts[1])
    entrance = int(parts[2])
    floor = int(parts[3])
    item = parts[4]
    if floor == 1:
        try:
            area_id = int(item)
            common_name = get_common_area_name(building, entrance, area_id)
            if common_name:
                await state.update_data(
                    building=building,
                    entrance=entrance,
                    floor=floor,
                    common_area=common_name,
                    location_type="common_area"
                )
                await callback.message.edit_text(f"✅ Выбрана общая зона: {common_name}")
                await state.set_state(TaskCreate.enter_title)
                await callback.message.answer("Введите заголовок заявки:", reply_markup=ReplyKeyboardRemove())
                await callback.answer()
                return
        except ValueError:
            pass
    apartment = int(item)
    await state.update_data(
        building=building,
        entrance=entrance,
        floor=floor,
        apartment=apartment,
        location_type="apartment"
    )
    await callback.message.edit_text(
        f"✅ Выбран адрес:\n"
        f"Корпус {building}, подъезд {entrance}, этаж {floor}, квартира {apartment}"
    )
    await state.set_state(TaskCreate.enter_title)
    await callback.message.answer("Введите заголовок заявки:", reply_markup=ReplyKeyboardRemove())
    await callback.answer()

# --- Парковка ---
@router.callback_query(StateFilter(TaskCreate.select_parking_floor), F.data.startswith("obj_parking_floor:"))
async def process_parking_floor(callback: CallbackQuery, state: FSMContext):
    _, building_str, floor_str = callback.data.split(":")
    building = int(building_str)
    floor = int(floor_str)
    await state.update_data(parking_floor=floor, parking_offset=0)
    spots = get_parking_spots(building, floor)
    await state.set_state(TaskCreate.select_parking_spot)
    await callback.message.edit_text(
        f"🚗 Выберите машиноместо на этаже {floor} (страница 1):",
        reply_markup=parking_spot_keyboard(building, floor, spots, 0)
    )
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_parking_spot), F.data.startswith("obj_parking_spot:"))
async def process_parking_spot(callback: CallbackQuery, state: FSMContext):
    _, building_str, floor_str, spot_str = callback.data.split(":")
    building = int(building_str)
    floor = int(floor_str)
    spot = int(spot_str)
    await state.update_data(
        building=building,
        parking_floor=floor,
        parking_spot=spot,
        location_type="parking"
    )
    await callback.message.edit_text(f"✅ Выбрано машиноместо {spot}")
    await state.set_state(TaskCreate.enter_title)
    await callback.message.answer("Введите заголовок заявки:", reply_markup=ReplyKeyboardRemove())
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_parking_spot), F.data.startswith("obj_parking_more:"))
async def parking_more(callback: CallbackQuery, state: FSMContext):
    _, building_str, floor_str, offset_str = callback.data.split(":")
    building = int(building_str)
    floor = int(floor_str)
    offset = int(offset_str)
    spots = get_parking_spots(building, floor)
    next_spots = spots[offset:offset+20]
    if not next_spots:
        await callback.answer("Больше нет мест", show_alert=True)
        return
    page_num = offset // 20 + 1
    await safe_delete_message(callback.message)
    kb = parking_spot_keyboard(building, floor, spots, offset)
    await callback.message.answer(
        f"🚗 Выберите машиноместо на этаже {floor} (страница {page_num}):",
        reply_markup=kb
    )
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_parking_spot), F.data.startswith("obj_parking_back:"))
async def parking_back(callback: CallbackQuery, state: FSMContext):
    _, building_str, floor_str, offset_str = callback.data.split(":")
    building = int(building_str)
    floor = int(floor_str)
    offset = int(offset_str)
    spots = get_parking_spots(building, floor)
    if offset < 0:
        offset = 0
    page_num = offset // 20 + 1
    await safe_delete_message(callback.message)
    kb = parking_spot_keyboard(building, floor, spots, offset)
    await callback.message.answer(
        f"🚗 Выберите машиноместо на этаже {floor} (страница {page_num}):",
        reply_markup=kb
    )
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_parking_spot), F.data.startswith("obj_back_parking_floor:"))
async def back_to_parking_floor(callback: CallbackQuery, state: FSMContext):
    building_id = int(callback.data.split(":")[1]) if len(callback.data.split(":")) > 1 else 2
    await state.set_state(TaskCreate.select_parking_floor)
    await callback.message.edit_text(
        "🚗 Выберите уровень паркинга:",
        reply_markup=parking_floor_keyboard(building_id, [-1, -2])
    )
    await callback.answer()

# --- Келлеры ---
@router.callback_query(StateFilter(TaskCreate.select_cellar), F.data.startswith("obj_cellar:"))
async def process_cellar(callback: CallbackQuery, state: FSMContext):
    _, building_str, cellar_str = callback.data.split(":")
    building = int(building_str)
    cellar = int(cellar_str)
    await state.update_data(
        building=building,
        cellar=cellar,
        location_type="cellar"
    )
    await callback.message.edit_text(f"✅ Выбран келлер {cellar}")
    await state.set_state(TaskCreate.enter_title)
    await callback.message.answer("Введите заголовок заявки:", reply_markup=ReplyKeyboardRemove())
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_cellar), F.data.startswith("obj_cellar_more:"))
async def cellar_more(callback: CallbackQuery, state: FSMContext):
    _, building_str, offset_str = callback.data.split(":")
    building = int(building_str)
    offset = int(offset_str)
    cellars = get_cellars(building)
    next_cellars = cellars[offset:offset+20]
    if not next_cellars:
        await callback.answer("Больше нет келлеров", show_alert=True)
        return
    page_num = offset // 20 + 1
    await safe_delete_message(callback.message)
    kb = cellar_keyboard(building, cellars, offset)
    await callback.message.answer(
        f"🔐 Выберите келлер для корпуса {building} (страница {page_num}):",
        reply_markup=kb
    )
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_cellar), F.data.startswith("obj_cellar_back:"))
async def cellar_back(callback: CallbackQuery, state: FSMContext):
    _, building_str, offset_str = callback.data.split(":")
    building = int(building_str)
    offset = int(offset_str)
    if offset < 0:
        offset = 0
    cellars = get_cellars(building)
    page_num = offset // 20 + 1
    await safe_delete_message(callback.message)
    kb = cellar_keyboard(building, cellars, offset)
    await callback.message.answer(
        f"🔐 Выберите келлер для корпуса {building} (страница {page_num}):",
        reply_markup=kb
    )
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_cellar), F.data.startswith("obj_back_building:"))
async def back_to_building_from_cellar(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TaskCreate.select_building)
    await callback.message.edit_text(
        "🏢 Выберите объект (корпус, паркинг или келлер):",
        reply_markup=building_keyboard()
    )
    await callback.answer()

# --- Навигация "Назад" для других состояний ---
@router.callback_query(StateFilter(TaskCreate.select_entrance), F.data.startswith("obj_back_building:"))
async def back_to_building_from_entrance(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TaskCreate.select_building)
    await callback.message.edit_text(
        "🏢 Выберите объект (корпус, паркинг или келлер):",
        reply_markup=building_keyboard()
    )
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_floor), F.data.startswith("obj_back_entrance:"))
async def back_to_entrance_from_floor(callback: CallbackQuery, state: FSMContext):
    building_id = int(callback.data.split(":")[1]) if len(callback.data.split(":")) > 1 else None
    if building_id:
        entrances = get_entrances(building_id)
        await state.set_state(TaskCreate.select_entrance)
        await callback.message.edit_text(
            f"🏢 Выберите подъезд для корпуса {building_id}:",
            reply_markup=entrance_keyboard(building_id, entrances)
        )
    else:
        await state.set_state(TaskCreate.select_building)
        await callback.message.edit_text(
            "🏢 Выберите объект (корпус, паркинг или келлер):",
            reply_markup=building_keyboard()
        )
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_floor), F.data.startswith("obj_back_building:"))
async def back_to_building_from_floor(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TaskCreate.select_building)
    await callback.message.edit_text(
        "🏢 Выберите объект (корпус, паркинг или келлер):",
        reply_markup=building_keyboard()
    )
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_apartment), F.data.startswith("obj_back_floor:"))
async def back_to_floor_from_apartment(callback: CallbackQuery, state: FSMContext):
    building_id = int(callback.data.split(":")[1]) if len(callback.data.split(":")) > 1 else None
    entrance = int(callback.data.split(":")[2]) if len(callback.data.split(":")) > 2 else None
    if building_id and entrance:
        floors = get_floors(building_id, entrance)
        await state.set_state(TaskCreate.select_floor)
        await callback.message.edit_text(
            f"🏗 Выберите этаж для подъезда {entrance} (корпус {building_id}):",
            reply_markup=floor_keyboard(building_id, entrance, floors)
        )
    else:
        await state.set_state(TaskCreate.select_building)
        await callback.message.edit_text(
            "🏢 Выберите объект (корпус, паркинг или келлер):",
            reply_markup=building_keyboard()
        )
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_apartment), F.data.startswith("obj_back_entrance:"))
async def back_to_entrance_from_apartment(callback: CallbackQuery, state: FSMContext):
    building_id = int(callback.data.split(":")[1]) if len(callback.data.split(":")) > 1 else None
    if building_id:
        entrances = get_entrances(building_id)
        await state.set_state(TaskCreate.select_entrance)
        await callback.message.edit_text(
            f"🏢 Выберите подъезд для корпуса {building_id}:",
            reply_markup=entrance_keyboard(building_id, entrances)
        )
    else:
        await state.set_state(TaskCreate.select_building)
        await callback.message.edit_text(
            "🏢 Выберите объект (корпус, паркинг или келлер):",
            reply_markup=building_keyboard()
        )
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_parking_floor), F.data.startswith("obj_back_building:"))
async def back_to_building_from_parking_floor(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TaskCreate.select_building)
    await callback.message.edit_text(
        "🏢 Выберите объект (корпус, паркинг или келлер):",
        reply_markup=building_keyboard()
    )
    await callback.answer()

# --- Остальные шаги ---
@router.message(StateFilter(TaskCreate.enter_title), F.text)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(TaskCreate.enter_description)
    await message.answer("Введите описание заявки:", reply_markup=ReplyKeyboardRemove())

@router.message(StateFilter(TaskCreate.enter_description), F.text)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(TaskCreate.enter_applicant_type)
    employee = await get_employee(message.from_user.id)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Жилец")],
            [KeyboardButton(text="👤 Сотрудник")],
            [KeyboardButton(text="👤 Я")],
        ],
        resize_keyboard=True
    )
    await message.answer("Кто является заявителем?", reply_markup=kb)

@router.message(StateFilter(TaskCreate.enter_applicant_type), F.text == "👤 Я")
async def process_applicant_type_self(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка: вы не зарегистрированы.")
        return
    await state.update_data(
        applicant_type="employee",
        applicant_name=employee.full_name,
        applicant_phone=employee.phone or ""
    )
    await state.set_state(TaskCreate.enter_priority)
    await message.answer(
        f"✅ Заявитель: {employee.full_name}, телефон: {employee.phone or 'не указан'}",
        reply_markup=priority_keyboard()
    )

@router.message(StateFilter(TaskCreate.enter_applicant_type), F.text.in_(["👤 Жилец", "👤 Сотрудник"]))
async def process_applicant_type(message: Message, state: FSMContext):
    app_type = "resident" if message.text == "👤 Жилец" else "employee"
    await state.update_data(applicant_type=app_type)
    await state.set_state(TaskCreate.enter_applicant_name)
    await message.answer("Введите ФИО заявителя:", reply_markup=ReplyKeyboardRemove())

@router.message(StateFilter(TaskCreate.enter_applicant_name), F.text)
async def process_applicant_name(message: Message, state: FSMContext):
    await state.update_data(applicant_name=message.text.strip())
    await state.set_state(TaskCreate.enter_applicant_phone)
    await message.answer("Введите телефон заявителя (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(StateFilter(TaskCreate.enter_applicant_phone), F.text)
async def process_applicant_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    await state.update_data(applicant_phone=phone if phone != "-" else "")
    await state.set_state(TaskCreate.enter_priority)
    await message.answer(
        "Выберите приоритет:",
        reply_markup=priority_keyboard()
    )

@router.callback_query(StateFilter(TaskCreate.enter_priority), F.data.startswith("priority:"))
async def process_priority(callback: CallbackQuery, state: FSMContext):
    priority = int(callback.data.split(":")[1])
    await state.update_data(priority=priority)
    await state.set_state(TaskCreate.enter_media)
    await callback.message.delete()
    await callback.message.answer(
        "🖼 Отправьте фото или видео (опционально).\n"
        "Можно отправить несколько файлов.\n"
        "Когда закончите, нажмите **Готово**:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="✅ Готово")]],
            resize_keyboard=True
        )
    )
    await callback.answer()

@router.message(StateFilter(TaskCreate.enter_media), F.photo)
async def process_media_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    if photos is None:
        photos = []
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Добавлено фото ({len(photos)})")

@router.message(StateFilter(TaskCreate.enter_media), F.video)
async def process_media_video(message: Message, state: FSMContext):
    data = await state.get_data()
    videos = data.get("videos", [])
    if videos is None:
        videos = []
    videos.append(message.video.file_id)
    await state.update_data(videos=videos)
    await message.answer(f"✅ Добавлено видео ({len(videos)})")

@router.message(StateFilter(TaskCreate.enter_media), F.text == "✅ Готово")
async def finish_media(message: Message, state: FSMContext):
    await state.set_state(TaskCreate.confirm)
    data = await state.get_data()
    address_parts = []
    if data.get('building'):
        address_parts.append(f"корп. {data['building']}")
    if data.get('entrance'):
        address_parts.append(f"под. {data['entrance']}")
    if data.get('floor'):
        address_parts.append(f"эт. {data['floor']}")
    if data.get('apartment'):
        address_parts.append(f"кв. {data['apartment']}")
    elif data.get('common_area'):
        address_parts.append(f"зона: {data['common_area']}")
    elif data.get('parking_spot'):
        address_parts.append(f"м. {data['parking_spot']}")
    elif data.get('cellar'):
        address_parts.append(f"к. {data['cellar']}")
    address = ", ".join(address_parts) if address_parts else "—"

    text = (
        f"📝 Проверьте данные заявки:\n\n"
        f"Заголовок: {data['title']}\n"
        f"Описание: {data['description']}\n"
        f"Адрес: {address}\n"
        f"Заявитель: {data.get('applicant_name')} ({data.get('applicant_type')})\n"
        f"Телефон: {data.get('applicant_phone') or '—'}\n"
        f"Приоритет: {data.get('priority')}\n"
        f"Фото: {len(data.get('photos', []))} шт.\n"
        f"Видео: {len(data.get('videos', []))} шт.\n\n"
        f"Подтвердить создание?"
    )
    await message.answer(text, reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Да, создать")], [KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))

@router.message(StateFilter(TaskCreate.confirm), F.text == "✅ Да, создать")
async def confirm_create(message: Message, state: FSMContext):
    data = await state.get_data()
    print(f"DEBUG confirm_create data: {data}")
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка.")
        await state.clear()
        return

    selection = data.get('object_selection', {})
    if selection.get('type') == 'parking':
        if not data.get('parking_spot'):
            data['parking_spot'] = selection.get('parking_spot')
            data['parking_floor'] = selection.get('parking_floor')
            data['building'] = selection.get('building')
    elif selection.get('type') == 'common_area':
        if not data.get('common_area'):
            data['common_area'] = selection.get('common_area')
            data['building'] = selection.get('building')
            data['entrance'] = selection.get('entrance')
            data['floor'] = selection.get('floor')
    elif selection.get('type') == 'apartment':
        if not data.get('apartment'):
            data['apartment'] = selection.get('apartment')
            data['building'] = selection.get('building')
            data['entrance'] = selection.get('entrance')
            data['floor'] = selection.get('floor')
    elif selection.get('type') == 'cellar':
        if not data.get('cellar'):
            data['cellar'] = selection.get('cellar')
            data['building'] = selection.get('building')

    try:
        task = await create_task(
            title=data['title'],
            description=data['description'],
            created_by=employee.id,
            building=data.get('building'),
            entrance=data.get('entrance'),
            floor=data.get('floor'),
            apartment=data.get('apartment'),
            location_type=data.get('location_type'),
            parking_level=data.get('parking_floor'),
            parking_spot=data.get('parking_spot'),
            cellar=data.get('cellar'),
            common_area=data.get('common_area'),
            applicant_type=data.get('applicant_type'),
            applicant_name=data.get('applicant_name'),
            applicant_phone=data.get('applicant_phone'),
            priority=data.get('priority', 3),
            photo_ids=data.get('photos', []),
            video_ids=data.get('videos', [])
        )
        await state.clear()
        await notify_admins_with_button(
            f"📢 Новая заявка #{task.id}: {task.title} создана сотрудником {employee.full_name}",
            "👁️ Посмотреть заявку",
            f"task:{task.id}"
        )
        if employee.role != UserRole.CONCIERGE:
            await notify_team_with_button(
                Team.TEAM_CONCIERGE,
                f"📢 Новая заявка #{task.id}: {task.title} создана сотрудником {employee.full_name}\nНазначьте исполнителя.",
                "👁️ Посмотреть заявку",
                f"task:{task.id}"
            )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Посмотреть заявку", callback_data=f"task:{task.id}")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        await message.answer(
            f"✅ Заявка #{task.id} создана!",
            reply_markup=kb
        )
        await message.answer("Выберите действие:", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", parse_mode=None)
        await state.clear()

@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    employee = await get_employee(callback.from_user.id)
    if employee:
        await callback.message.delete()
        await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard(employee.role))
    await callback.answer()

@router.message(StateFilter(TaskCreate.confirm), F.text == "❌ Отмена")
async def cancel_create(message: Message, state: FSMContext):
    await state.clear()
    employee = await get_employee(message.from_user.id)
    await message.answer("❌ Создание отменено", reply_markup=main_menu_keyboard(employee.role) if employee else None)

@router.callback_query(F.data == "obj_cancel")
async def cancel_object_selection(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    employee = await get_employee(callback.from_user.id)
    await callback.message.answer("Действие отменено", reply_markup=main_menu_keyboard(employee.role) if employee else None)
    await callback.answer()
