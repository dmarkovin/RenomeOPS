from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from app.services.employees.service import get_employee
from app.services.services.service import (
    get_all_services,
    get_service,
    create_service_order,
    get_user_orders,
    update_order_status,
    get_order
)
from app.database.models import UserRole
from app.keyboards.services import service_catalog_keyboard, service_order_status_keyboard, service_admin_keyboard
from app.keyboards.object_navigation import building_keyboard, apartment_keyboard, parking_floor_keyboard, parking_spot_keyboard, cellar_keyboard
from app.utils.object_navigation import get_apartments, get_parking_spots, get_cellars
from app.keyboards.main_menu import main_menu_keyboard

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
    employee = await get_employee(callback.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE):
        await callback.answer("У вас нет прав заказывать услуги", show_alert=True)
        return

    await state.update_data(service_id=service_id, service_name=service.name)
    await state.set_state(ServiceOrderState.select_object)
    await callback.message.edit_text(
        f"📝 Заказ услуги: {service.name}\n"
        f"Цена: {service.price} руб.\n\n"
        "Выберите объект (квартиру, паркинг или келлер):",
        reply_markup=building_keyboard()
    )
    await callback.answer()

# Обработчики выбора объекта (квартира, паркинг, келлер)
@router.callback_query(StateFilter(ServiceOrderState.select_object), F.data.startswith("obj_apartment:"))
async def handle_apartment_selection(callback: CallbackQuery, state: FSMContext):
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
    await callback.message.edit_text(f"✅ Выбрана квартира {apartment}")
    await state.set_state(ServiceOrderState.comment)
    await callback.message.answer("Введите комментарий (или '-' для пропуска):")
    await callback.answer()

@router.callback_query(StateFilter(ServiceOrderState.select_object), F.data.startswith("obj_parking_spot:"))
async def handle_parking_selection(callback: CallbackQuery, state: FSMContext):
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
    await callback.message.edit_text(f"✅ Выбрано машиноместо {spot}")
    await state.set_state(ServiceOrderState.comment)
    await callback.message.answer("Введите комментарий (или '-' для пропуска):")
    await callback.answer()

@router.callback_query(StateFilter(ServiceOrderState.select_object), F.data.startswith("obj_cellar:"))
async def handle_cellar_selection(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    building = int(parts[1])
    cellar = int(parts[2])
    await state.update_data(object_data={
        "building": building,
        "cellar": cellar,
        "type": "cellar"
    })
    await callback.message.edit_text(f"✅ Выбран келлер {cellar}")
    await state.set_state(ServiceOrderState.comment)
    await callback.message.answer("Введите комментарий (или '-' для пропуска):")
    await callback.answer()

# Для выбора паркинга – сначала уровень, потом место
@router.callback_query(StateFilter(ServiceOrderState.select_object), F.data.startswith("obj_parking_floor:"))
async def handle_parking_floor(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    building = int(parts[1])
    floor = int(parts[2])
    await state.update_data(parking_building=building, parking_level=floor)
    spots = get_parking_spots(building, floor)
    await callback.message.edit_text(
        f"Выберите машиноместо на уровне {floor}:",
        reply_markup=parking_spot_keyboard(building, floor, spots)
    )
    await callback.answer()

# Возврат к выбору объекта
@router.callback_query(F.data == "service_back")
async def back_to_catalog(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    employee = await get_employee(callback.from_user.id)
    if employee:
        await callback.message.answer("Меню услуг", reply_markup=main_menu_keyboard(employee.role))
    await callback.answer()

# Комментарий
@router.message(ServiceOrderState.comment)
async def process_comment(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(comment=text if text != "-" else "")
    await state.set_state(ServiceOrderState.photo)
    await message.answer(
        "🖼 Пришлите фото (опционально) или нажмите **Готово**:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="✅ Готово")]],
            resize_keyboard=True
        )
    )

# Фото
@router.message(ServiceOrderState.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Добавлено фото ({len(photos)})")

@router.message(ServiceOrderState.photo, F.text == "✅ Готово")
async def finish_order(message: Message, state: FSMContext):
    await state.set_state(ServiceOrderState.confirm)
    data = await state.get_data()
    text = (
        f"📝 Проверьте заказ:\n\n"
        f"Услуга: {data.get('service_name')}\n"
        f"Объект: {data.get('object_data')}\n"
        f"Комментарий: {data.get('comment') or '—'}\n"
        f"Фото: {len(data.get('photos', []))} шт.\n\n"
        f"Подтвердить заказ?"
    )
    await message.answer(text, reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="✅ Да, заказать")], [types.KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))

@router.message(ServiceOrderState.confirm, F.text == "✅ Да, заказать")
async def confirm_order(message: Message, state: FSMContext):
    data = await state.get_data()
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка.")
        await state.clear()
        return
    try:
        order = await create_service_order(
            service_id=data['service_id'],
            user_id=employee.id,
            object_data=data['object_data'],
            comment=data.get('comment', ''),
            photo_ids=data.get('photos', [])
        )
        await state.clear()
        await message.answer(
            f"✅ Заказ #{order.id} создан! Статус: {order.status}",
            reply_markup=main_menu_keyboard(employee.role)
        )
        # Уведомление админам
        from app.services.notification_service import notify_admins
        await notify_admins(f"📢 Новый заказ услуги #{order.id} от {employee.full_name}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", parse_mode=None)
        await state.clear()

@router.message(ServiceOrderState.confirm, F.text == "❌ Отмена")
async def cancel_order(message: Message, state: FSMContext):
    await state.clear()
    employee = await get_employee(message.from_user.id)
    await message.answer("Отменено", reply_markup=main_menu_keyboard(employee.role) if employee else None)

# Статусы заказа
@router.callback_query(F.data.startswith("order_pay:"))
async def pay_order(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    order = await update_order_status(order_id, "paid")
    if order:
        await callback.answer("✅ Оплачен")
        await show_order_card(callback)
    else:
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("order_complete:"))
async def complete_order(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    order = await update_order_status(order_id, "completed")
    if order:
        await callback.answer("✅ Выполнен")
        await show_order_card(callback)
    else:
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("order_cancel:"))
async def cancel_order_admin(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    order = await update_order_status(order_id, "cancelled")
    if order:
        await callback.answer("❌ Отменён")
        await show_order_card(callback)
    else:
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("order:"))
async def show_order_card(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    order = await get_order(order_id)
    if not order:
        await callback.answer("Не найден", show_alert=True)
        return
    service = await get_service(order.service_id)
    text = (
        f"📦 Заказ #{order.id}\n"
        f"Услуга: {service.name if service else '—'}\n"
        f"Цена: {service.price if service else '—'} руб.\n"
        f"Статус: {order.status}\n"
        f"Объект: корпус {order.building or '—'} | квартира {order.apartment or '—'}\n"
        f"Комментарий: {order.comment or '—'}\n"
        f"Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}"
    )
    await callback.message.edit_text(text, reply_markup=service_order_status_keyboard(order.id))
    await callback.answer()

# Список заказов пользователя
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
