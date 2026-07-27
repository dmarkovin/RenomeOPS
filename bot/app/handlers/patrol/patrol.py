from aiogram.types import ReplyKeyboardRemove
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter

from app.services.employees.service import get_employee
from app.services.patrol.service import create_patrol, get_patrol, get_patrols, complete_patrol
from app.services.tasks.service import create_task, assign_task_to_team
from app.services.notification_service import notify_concierges
from app.database.models import UserRole, Team
from app.keyboards.patrol import patrol_list_keyboard, patrol_action_keyboard, patrol_main_menu_keyboard
from app.keyboards.main_menu import main_menu_keyboard

router = Router()

class PatrolCreate(StatesGroup):
    route = State()
    notes = State()
    photo = State()
    confirm = State()

@router.message(F.text == "🚶 Обходы")
async def patrol_menu(message: Message, page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.SECURITY, UserRole.ADMIN, UserRole.CONCIERGE):
        await message.answer("У вас нет прав.")
        return

    limit = 10
    offset = (page - 1) * limit
    patrols = await get_patrols(user_id=employee.id, limit=limit, offset=offset)
    total = len(patrols)
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    if not patrols:
        await message.answer("Нет обходов.", reply_markup=patrol_main_menu_keyboard())
        return

    text = "🚶 Список обходов:\n\n"
    for p in patrols:
        status_emoji = "🔄" if p.status == "active" else "✅"
        text += f"{status_emoji} #{p.id} {p.route} ({p.status})\n"
    await message.answer(text, reply_markup=patrol_list_keyboard(patrols, page, total_pages))


@router.message(F.text == "➕ Новый обход")
async def start_create_patrol(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role != UserRole.SECURITY:
        await message.answer("Только для охраны.")
        return
    await state.clear()
    await state.set_state(PatrolCreate.route)
    await message.answer("Введите маршрут обхода:", reply_markup=ReplyKeyboardRemove())


@router.message(PatrolCreate.route)
async def process_route(message: Message, state: FSMContext):
    await state.update_data(route=message.text.strip())
    await state.set_state(PatrolCreate.notes)
    await message.answer("Введите заметки по обходу (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())


@router.message(PatrolCreate.notes)
async def process_notes(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(notes=text if text != "-" else "")
    await state.set_state(PatrolCreate.photo)
    await message.answer("🖼 Пришлите фото (опционально) или нажмите **Готово**:", reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="✅ Готово")]],
        resize_keyboard=True
    ))


@router.message(PatrolCreate.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Добавлено фото ({len(photos)})")


@router.message(PatrolCreate.photo, F.text == "✅ Готово")
async def finish_photo(message: Message, state: FSMContext):
    await state.set_state(PatrolCreate.confirm)
    data = await state.get_data()
    text = (
        f"📝 Проверьте данные обхода:\n\n"
        f"Маршрут: {data['route']}\n"
        f"Заметки: {data.get('notes') or '—'}\n"
        f"Фото: {len(data.get('photos', []))} шт.\n\n"
        f"Подтвердить создание?"
    )
    await message.answer(text, reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="✅ Да, создать")], [types.KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))


@router.message(PatrolCreate.confirm, F.text == "✅ Да, создать")
async def confirm_create(message: Message, state: FSMContext):
    data = await state.get_data()
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка.")
        await state.clear()
        return
    try:
        # Создаём задачу для консьержей
        task = await create_task(
            title=f"Обход: {data['route']}",
            description=data.get('notes', ''),
            created_by=employee.id,
            location_type="patrol",
            priority=3,
            photo_ids=data.get('photos', []),
            is_paid=False,
            assigned_team=Team.TEAM_CONCIERGE  # назначаем на команду консьержей
        )

        # Создаём запись об обходе
        patrol = await create_patrol(
            route=data['route'],
            notes=data.get('notes'),
            photo_ids=data.get('photos', []),
            created_by=employee.id,
            task_id=task.id
        )

        # Уведомляем консьержей
        await notify_concierges(
            f"🚶 Новый обход #{patrol.id} от {employee.full_name} создан. "
            f"Задача #{task.id} назначена на вашу команду."
        )

        await state.clear()
        await message.answer(
            f"✅ Обход #{patrol.id} создан!\n"
            f"📋 Создана задача #{task.id} для консьержей.",
            reply_markup=patrol_main_menu_keyboard()
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", parse_mode=None)
        await state.clear()


@router.message(PatrolCreate.confirm, F.text == "❌ Отмена")
async def cancel_create(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено", reply_markup=patrol_main_menu_keyboard())


@router.callback_query(F.data.startswith("patrol:"))
async def show_patrol_card(callback: CallbackQuery):
    patrol_id = int(callback.data.split(":")[1])
    p = await get_patrol(patrol_id)
    if not p:
        await callback.answer("Не найден", show_alert=True)
        return
    text = (
        f"🚶 Обход #{p.id}\n"
        f"Маршрут: {p.route}\n"
        f"Заметки: {p.notes or '—'}\n"
        f"Статус: {p.status}\n"
        f"Начало: {p.start_time.strftime('%d.%m.%Y %H:%M')}\n"
        f"Окончание: {p.end_time.strftime('%d.%m.%Y %H:%M') if p.end_time else '—'}\n"
        f"Задача: #{p.task_id if p.task_id else '—'}"
    )
    await callback.message.edit_text(text, reply_markup=patrol_action_keyboard(p.id, p.status))
    await callback.answer()


@router.callback_query(F.data.startswith("patrol_complete:"))
async def patrol_complete(callback: CallbackQuery):
    patrol_id = int(callback.data.split(":")[1])
    p = await complete_patrol(patrol_id)
    if p:
        await callback.answer("✅ Обход завершён")
        await show_patrol_card(callback)
    else:
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("patrol_page:"))
async def paginate_patrols(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    await patrol_menu(callback.message, page)
    await callback.answer()


@router.callback_query(F.data == "patrol_back")
async def back_to_patrol_menu(callback: CallbackQuery):
    await callback.message.delete()
    employee = await get_employee(callback.from_user.id)
    await callback.message.answer("Меню обходов", reply_markup=patrol_main_menu_keyboard())
    await callback.answer()
