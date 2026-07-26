from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.services.employees.service import get_employee
from app.services.tasks.service import create_task
from app.services.notification_service import notify_admins
from app.database.models import UserRole
from app.keyboards.main_menu import main_menu_keyboard

router = Router()

class TaskCreate(StatesGroup):
    title = State()
    description = State()
    building = State()
    apartment = State()
    priority = State()
    photo = State()
    confirm = State()

@router.message(F.text == "➕ Создать заявку")
async def start_create_task(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE):
        await message.answer("У вас нет прав для создания заявок.")
        return
    await state.clear()
    await state.set_state(TaskCreate.title)
    await message.answer("📝 Введите **название** заявки:")

@router.message(TaskCreate.title)
async def task_title(message: Message, state: FSMContext):
    if len(message.text.strip()) < 3:
        await message.answer("Название должно быть не короче 3 символов. Попробуйте снова.")
        return
    await state.update_data(title=message.text.strip())
    await state.set_state(TaskCreate.description)
    await message.answer("📄 Введите **описание** заявки (или '-' для пропуска):")

@router.message(TaskCreate.description)
async def task_description(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(description=text if text != "-" else None)
    await state.set_state(TaskCreate.building)
    await message.answer("🏢 Введите **корпус** (или '-' для пропуска):")

@router.message(TaskCreate.building)
async def task_building(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(building=text if text != "-" else None)
    await state.set_state(TaskCreate.apartment)
    await message.answer("🏠 Введите **квартиру** (или '-' для пропуска):")

@router.message(TaskCreate.apartment)
async def task_apartment(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(apartment=text if text != "-" else None)
    await state.set_state(TaskCreate.priority)
    await message.answer("🔢 Введите **приоритет** (число от 1 до 5, по умолчанию 3):")

@router.message(TaskCreate.priority)
async def task_priority(message: Message, state: FSMContext):
    try:
        priority = int(message.text.strip())
        if priority < 1 or priority > 5:
            raise ValueError
    except ValueError:
        priority = 3
        await message.answer("⚠️ Использую приоритет по умолчанию (3).")
    await state.update_data(priority=priority)
    await state.set_state(TaskCreate.photo)
    await message.answer(
        "🖼 Пришлите **фото** (опционально) или нажмите **Готово**:",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="✅ Готово")]],
            resize_keyboard=True
        )
    )

@router.message(TaskCreate.photo, F.photo)
async def task_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Фото добавлено ({len(photos)} шт.). Можете добавить ещё или нажать **Готово**.")

@router.message(TaskCreate.photo, F.text == "✅ Готово")
async def task_photo_ready(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    title = data.get("title")
    description = data.get("description")
    building = data.get("building")
    apartment = data.get("apartment")
    priority = data.get("priority", 3)

    text = (
        f"📝 **Проверьте данные заявки:**\n\n"
        f"Название: {title}\n"
        f"Описание: {description or '—'}\n"
        f"Корпус: {building or '—'}\n"
        f"Квартира: {apartment or '—'}\n"
        f"Приоритет: {priority}\n"
        f"Фото: {len(photos)} шт.\n\n"
        f"Подтвердить создание?"
    )
    await state.set_state(TaskCreate.confirm)
    await message.answer(
        text,
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="✅ Да, создать")],
                [types.KeyboardButton(text="❌ Отмена")],
            ],
            resize_keyboard=True
        )
    )

@router.message(TaskCreate.confirm, F.text == "✅ Да, создать")
async def confirm_create_task(message: Message, state: FSMContext):
    data = await state.get_data()
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        await state.clear()
        return

    try:
        task = await create_task(
            title=data.get("title"),
            description=data.get("description"),
            created_by=employee.id,
            building=data.get("building"),
            apartment=data.get("apartment"),
            priority=data.get("priority", 3),
            photo_ids=data.get("photos", []),
        )
        await state.clear()
        await notify_admins(f"📢 Новая заявка #{task.id}: {task.title} создана сотрудником {employee.full_name}")
        await message.answer(
            f"✅ Заявка #{task.id} создана!",
            reply_markup=main_menu_keyboard(employee.role)
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при создании заявки: {str(e)}")
        await state.clear()

@router.message(TaskCreate.confirm, F.text == "❌ Отмена")
async def cancel_create_task(message: Message, state: FSMContext):
    await state.clear()
    employee = await get_employee(message.from_user.id)
    await message.answer(
        "❌ Создание заявки отменено.",
        reply_markup=main_menu_keyboard(employee.role) if employee else None
    )

@router.message(TaskCreate.confirm)
async def invalid_confirmation(message: Message):
    await message.answer("Пожалуйста, используйте кнопки для подтверждения или отмены.")
