from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.services.employees.service import get_employee
from app.services.services.service import get_all_services, get_service, create_service_order, get_user_orders
from app.database.models import UserRole
from app.keyboards.services import service_catalog_keyboard, service_details_keyboard
from app.keyboards.object_navigation import building_keyboard
from app.handlers.object_navigation import router as object_navigation_router

router = Router()

class ServiceOrderState(StatesGroup):
    select_object = State()
    comment = State()
    photo = State()
    confirm = State()

@router.message(F.text == "💳 Платные услуги")
async def show_service_catalog(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    services = await get_all_services(active_only=True)
    if not services:
        await message.answer("Услуг пока нет.")
        return
    await message.answer(
        "💰 Каталог платных услуг:",
        reply_markup=service_catalog_keyboard(services)
    )

@router.callback_query(F.data.startswith("service_order:"))
async def start_order_service(callback: CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split(":")[1])
    service = await get_service(service_id)
    if not service:
        await callback.answer("Услуга не найдена", show_alert=True)
        return
    # Проверка, что пользователь может заказать
    employee = await get_employee(callback.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE):
        await callback.answer("У вас нет прав заказывать услуги", show_alert=True)
        return

    await state.update_data(service_id=service_id)
    await state.set_state(ServiceOrderState.select_object)
    await callback.message.edit_text(
        f"📝 Заказ услуги: {service.name}\n"
        f"Цена: {service.price} руб.\n\n"
        "Выберите объект (квартиру, паркинг или келлер):",
        reply_markup=building_keyboard()
    )
    await callback.answer()

# Здесь мы будем использовать общий обработчик навигации из object_navigation.py,
# но нам нужно перехватить выбор объекта и сохранить его.
# Мы можем добавить проверку состояния в object_navigation.py или сделать отдельный хендлер.
# Пока оставим как есть, а потом доработаем.

# Временно: после выбора объекта мы должны перейти к следующему шагу.
# Но сейчас мы не можем легко перехватить выбор из object_navigation.py,
# поэтому мы пока сделаем заглушку: после выбора объекта пользователь нажимает "Готово".

# Для демонстрации я дам упрощённый вариант: после выбора объекта мы сохраняем его и переходим к комментарию.
# Я добавлю обработчик для callback'ов от object_navigation, которые будут сохранять результат в состоянии.

# Это временное решение, чтобы не переписывать object_navigation.py.

@router.callback_query(F.data.startswith("obj_apartment:"))
async def handle_apartment_selection(callback: CallbackQuery, state: FSMContext):
    # Проверяем, что мы в процессе заказа
    data = await state.get_data()
    if "service_id" not in data:
        await callback.answer("Действие неактивно", show_alert=True)
        return
    # Парсим данные
    parts = callback.data.split(":")
    building = int(parts[1])
    entrance = int(parts[2])
    floor = int(parts[3])
    apartment = int(parts[4])
    await state.update_data(object_data={
        "building": building,
        "entrance": entrance,
        "floor": floor,
        "apartment": apartment,
        "type": "apartment"
    })
    await callback.message.edit_text(f"✅ Выбрана квартира {apartment} (корпус {building})")
    await state.set_state(ServiceOrderState.comment)
    await callback.message.answer("Введите комментарий (или '-' для пропуска):")
    await callback.answer()

@router.callback_query(F.data.startswith("obj_parking_spot:"))
async def handle_parking_selection(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if "service_id" not in data:
        await callback.answer("Действие неактивно", show_alert=True)
        return
    parts = callback.data.split(":")
    building = int(parts[1])
    floor = int(parts[2])
    spot = int(parts[3])
    await state.update_data(object_data={
        "building": building,
        "parking_floor": floor,
        "parking_spot": spot,
        "type": "parking"
    })
    await callback.message.edit_text(f"✅ Выбрано машиноместо {spot} (этаж {floor})")
    await state.set_state(ServiceOrderState.comment)
    await callback.message.answer("Введите комментарий (или '-' для пропуска):")
    await callback.answer()

@router.callback_query(F.data.startswith("obj_cellar:"))
async def handle_cellar_selection(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if "service_id" not in data:
        await callback.answer("Действие неактивно", show_alert=True)
        return
    parts = callback.data.split(":")
    building = int(parts[1])
    cellar = int(parts[2])
    await state.update_data(object_data={
        "building": building,
        "cellar": cellar,
        "type": "cellar"
    })
    await callback.message.edit_text(f"✅ Выбран келлер {cellar} (корпус {building})")
    await state.set_state(ServiceOrderState.comment)
    await callback.message.answer("Введите комментарий (или '-' для пропуска):")
    await callback.answer()

@router.message(ServiceOrderState.comment)
async def process_comment(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(comment=text if text != "-" else "")
    await state.set_state(ServiceOrderState.photo)
    await message.answer(
        "🖼 Пришлите фото (опционально) или нажмите 'Готово':",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="✅ Готово")]],
            resize_keyboard=True
        )
    )

@router.message(ServiceOrderState.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Добавлено фото ({len(photos)} шт.)")

@router.message(ServiceOrderState.photo, F.text == "✅ Готово")
async def finish_order(message: Message, state: FSMContext):
    data = await state.get_data()
    service_id = data.get("service_id")
    object_data = data.get("object_data")
    comment = data.get("comment", "")
    photos = data.get("photos", [])
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка")
        await state.clear()
        return
    try:
        order = await create_service_order(
            service_id=service_id,
            user_id=employee.id,
            object_data=object_data,
            comment=comment,
            photo_ids=photos
        )
        await message.answer(
            f"✅ Заказ #{order.id} создан!\n"
            f"Услуга: {await get_service(service_id)}.name\n"
            f"Статус: {order.status}\n"
            f"Комментарий: {comment or '—'}",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="💳 Платные услуги")]],
                resize_keyboard=True
            )
        )
        # Уведомление админам
        from app.services.notification_service import notify_admins
        await notify_admins(f"📢 Новый заказ услуги #{order.id} от {employee.full_name}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    await state.clear()

@router.message(F.text == "📋 Мои заказы")
async def show_user_orders(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
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

# Импорт для ReplyKeyboardMarkup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
