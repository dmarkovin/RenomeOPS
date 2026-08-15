from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter

from app.services.employees.service import get_employee
from app.services.tasks.service import create_task, assign_task_to_team
from app.services.notification_service import notify_admins, notify_team_with_button
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
from app.utils.object_navigation import get_entrances, get_floors, get_apartments, get_parking_spots, get_cellars

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
        await message.answer("У вас нет прав на создание заявки.")
        return
    await state.clear()
    await state.set_state(TaskCreate.select_building)
    await message.answer(
        "🏢 Выберите объект (корпус, паркинг или келлер):",
        reply_markup=building_keyboard()
    )

@router.callback_query(StateFilter(TaskCreate.select_building), F.data.startswith("obj_building:"))
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

@router.callback_query(StateFilter(TaskCreate.select_building), F.data == "obj_parking")
async def process_parking(callback: CallbackQuery, state: FSMContext):
    await state.update_data(object_type="parking")
    await callback.message.edit_text(
        "🚗 Выберите уровень паркинга:",
        reply_markup=parking_floor_keyboard(2, [-1, -2])
    )
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_entrance), F.data.startswith("obj_entrance:"))
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
    await callback.message.edit_text(
        f"🏠 Выберите на этаже {floor}:",
        reply_markup=apartment_keyboard(building_id, entrance, floor, apartments)
    )
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_apartment), F.data.startswith("obj_apartment:"))
async def process_apartment(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    if len(parts) >= 5 and not parts[4].isdigit():
        # Общая зона
        _, building_str, entrance_str, floor_str, common_name = parts
        building = int(building_str)
        entrance = int(entrance_str)
        floor = int(floor_str)
        await state.update_data(
            building=building,
            entrance=entrance,
            floor=floor,
            location_type="common_area",
            common_area=common_name
        )
        await callback.message.edit_text(f"✅ Выбрана общая зона: {common_name}")
    else:
        # Квартира
        _, building_str, entrance_str, floor_str, apt_str = parts
        building = int(building_str)
        entrance = int(entrance_str)
        floor = int(floor_str)
        apartment = int(apt_str)
        await state.update_data(
            building=building,
            entrance=entrance,
            floor=floor,
            apartment=apartment,
            location_type="apartment"
        )
        await callback.message.edit_text(f"✅ Выбрана квартира {apartment}")
    await state.set_state(TaskCreate.enter_title)
    await callback.message.answer("Введите заголовок заявки:", reply_markup=ReplyKeyboardRemove())
    await callback.answer()

@router.callback_query(StateFilter(TaskCreate.select_parking_floor), F.data.startswith("obj_parking_floor:"))
async def process_parking_floor(callback: CallbackQuery, state: FSMContext):
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
    await state.set_state(TaskCreate.enter_photo)
    await callback.message.delete()
    await callback.message.answer(
        "🖼 Пришлите фото или видео (опционально). После отправки нажмите **Готово**:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="✅ Готово")]],
            resize_keyboard=True
        )
    )
    await callback.answer()

# Обработчик фото
@router.message(StateFilter(TaskCreate.enter_photo), F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Добавлено фото ({len(photos)})")

# Обработчик видео
@router.message(StateFilter(TaskCreate.enter_photo), F.video)
async def process_video(message: Message, state: FSMContext):
    data = await state.get_data()
    videos = data.get("videos", [])
    videos.append(message.video.file_id)
    await state.update_data(videos=videos)
    await message.answer(f"✅ Добавлено видео ({len(videos)})")

@router.message(StateFilter(TaskCreate.enter_photo), F.text == "✅ Готово")
async def finish_photo(message: Message, state: FSMContext):
    await state.set_state(TaskCreate.confirm)
    data = await state.get_data()
    text = (
        f"📝 Проверьте данные заявки:\n\n"
        f"Заголовок: {data['title']}\n"
        f"Описание: {data['description']}\n"
        f"Объект: {data.get('building') or '—'} {data.get('apartment') or data.get('parking_spot') or data.get('cellar') or data.get('common_area') or '—'}\n"
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
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка.")
        await state.clear()
        return
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
            applicant_type=data.get('applicant_type'),
            applicant_name=data.get('applicant_name'),
            applicant_phone=data.get('applicant_phone'),
            priority=data.get('priority', 3),
            photo_ids=data.get('photos', []),
            video_ids=data.get('videos', [])
        )
        await state.clear()
        await notify_admins(f"📢 Новая заявка #{task.id}: {task.title} создана сотрудником {employee.full_name}", task_id=task.id)
        if employee.role != UserRole.CONCIERGE:
            await notify_team_with_button(
                Team.TEAM_CONCIERGE,
                f"📢 Новая заявка #{task.id}: {task.title} создана сотрудником {employee.full_name}\nНазначьте исполнителя.",
                task.id
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
