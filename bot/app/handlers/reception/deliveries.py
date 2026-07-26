from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter

from app.services.employees.service import get_employee
from app.services.reception.delivery_service import (
    create_delivery, get_all_deliveries, get_delivery, update_delivery_status
)
from app.database.models import UserRole
from app.keyboards.reception import delivery_list_keyboard, delivery_action_keyboard
from app.keyboards.main_menu import main_menu_keyboard

router = Router()

class DeliveryCreate(StatesGroup):
    recipient = State()
    apartment = State()
    courier = State()
    comment = State()
    photo = State()
    confirm = State()

@router.message(F.text == "📦 Доставка")
async def delivery_menu(message: Message, page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE):
        await message.answer("У вас нет прав.")
        return
    # Показываем список доставок (все активные)
    limit = 10
    offset = (page - 1) * limit
    deliveries = await get_all_deliveries(limit=limit, offset=offset, status=None)
    total = len(await get_all_deliveries())  # упрощённо, для демо
    total_pages = (total + limit - 1) // limit
    if not deliveries:
        await message.answer("Нет доставок. Создайте новую.", reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="➕ Новая доставка")], [types.KeyboardButton(text="⬅️ Назад")]],
            resize_keyboard=True
        ))
        return
    text = "📦 Список доставок:\n\n"
    for d in deliveries:
        status_emoji = "🟡" if d.status == "pending" else "🔵" if d.status == "received" else "✅"
        text += f"{status_emoji} #{d.id} {d.recipient} (кв.{d.apartment or '—'}) - {d.status}\n"
    await message.answer(text, reply_markup=delivery_list_keyboard(deliveries, page, total_pages))

@router.message(F.text == "➕ Новая доставка")
async def start_create_delivery(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE):
        await message.answer("Нет прав.")
        return
    await state.clear()
    await state.set_state(DeliveryCreate.recipient)
    await message.answer("Введите ФИО получателя:")

@router.message(DeliveryCreate.recipient)
async def process_recipient(message: Message, state: FSMContext):
    await state.update_data(recipient=message.text.strip())
    await state.set_state(DeliveryCreate.apartment)
    await message.answer("Введите номер квартиры (или '-' для пропуска):")

@router.message(DeliveryCreate.apartment)
async def process_apartment(message: Message, state: FSMContext):
    text = message.text.strip()
    apartment = int(text) if text.isdigit() else None
    await state.update_data(apartment=apartment)
    await state.set_state(DeliveryCreate.courier)
    await message.answer("Введите название курьерской службы (или '-' для пропуска):")

@router.message(DeliveryCreate.courier)
async def process_courier(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(courier=text if text != "-" else "")
    await state.set_state(DeliveryCreate.comment)
    await message.answer("Введите комментарий (или '-' для пропуска):")

@router.message(DeliveryCreate.comment)
async def process_comment(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(comment=text if text != "-" else "")
    await state.set_state(DeliveryCreate.photo)
    await message.answer("🖼 Пришлите фото (опционально) или нажмите **Готово**:", reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="✅ Готово")]],
        resize_keyboard=True
    ))

@router.message(DeliveryCreate.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Добавлено фото ({len(photos)})")

@router.message(DeliveryCreate.photo, F.text == "✅ Готово")
async def finish_photos(message: Message, state: FSMContext):
    await state.set_state(DeliveryCreate.confirm)
    data = await state.get_data()
    text = (
        f"📦 Проверьте данные:\n\n"
        f"Получатель: {data['recipient']}\n"
        f"Квартира: {data.get('apartment') or '—'}\n"
        f"Курьер: {data.get('courier') or '—'}\n"
        f"Комментарий: {data.get('comment') or '—'}\n"
        f"Фото: {len(data.get('photos', []))} шт.\n\n"
        f"Подтвердить создание?"
    )
    await message.answer(text, reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="✅ Да, создать")], [types.KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))

@router.message(DeliveryCreate.confirm, F.text == "✅ Да, создать")
async def confirm_delivery(message: Message, state: FSMContext):
    data = await state.get_data()
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка")
        await state.clear()
        return
    try:
        delivery = await create_delivery(
            recipient=data['recipient'],
            apartment=data.get('apartment'),
            courier_service=data.get('courier'),
            comment=data.get('comment'),
            created_by=employee.id,
            photo_ids=data.get('photos', [])
        )
        await state.clear()
        await message.answer(f"✅ Доставка #{delivery.id} создана!", reply_markup=main_menu_keyboard(employee.role))
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()

@router.message(DeliveryCreate.confirm, F.text == "❌ Отмена")
async def cancel_delivery(message: Message, state: FSMContext):
    await state.clear()
    employee = await get_employee(message.from_user.id)
    await message.answer("Отменено", reply_markup=main_menu_keyboard(employee.role) if employee else None)

# Callback'и
@router.callback_query(F.data.startswith("delivery:"))
async def show_delivery_card(callback: CallbackQuery):
    delivery_id = int(callback.data.split(":")[1])
    delivery = await get_delivery(delivery_id)
    if not delivery:
        await callback.answer("Не найдено", show_alert=True)
        return
    text = (
        f"📦 Доставка #{delivery.id}\n"
        f"Получатель: {delivery.recipient}\n"
        f"Квартира: {delivery.apartment or '—'}\n"
        f"Курьер: {delivery.courier_service or '—'}\n"
        f"Статус: {delivery.status}\n"
        f"Комментарий: {delivery.comment or '—'}\n"
        f"Создана: {delivery.created_at.strftime('%d.%m.%Y %H:%M')}"
    )
    await callback.message.edit_text(text, reply_markup=delivery_action_keyboard(delivery.id, delivery.status))
    await callback.answer()

@router.callback_query(F.data.startswith("delivery_receive:"))
async def receive_delivery(callback: CallbackQuery):
    delivery_id = int(callback.data.split(":")[1])
    delivery = await update_delivery_status(delivery_id, "received")
    if delivery:
        await callback.answer("✅ Отмечено как получено")
        await show_delivery_card(callback)
    else:
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("delivery_complete:"))
async def complete_delivery(callback: CallbackQuery):
    delivery_id = int(callback.data.split(":")[1])
    delivery = await update_delivery_status(delivery_id, "completed")
    if delivery:
        await callback.answer("✅ Завершено")
        await show_delivery_card(callback)
    else:
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("delivery_photo:"))
async def delivery_photo(callback: CallbackQuery):
    delivery_id = int(callback.data.split(":")[1])
    delivery = await get_delivery(delivery_id)
    if not delivery or not delivery.photo_ids:
        await callback.answer("Нет фото", show_alert=True)
        return
    # Отправляем первое фото
    await callback.message.answer_photo(delivery.photo_ids[0])
    await callback.answer()

@router.callback_query(F.data.startswith("delivery_page:"))
async def paginate_deliveries(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    await delivery_menu(callback.message, page)  # reuse
    await callback.answer()

@router.callback_query(F.data == "delivery_back")
async def back_to_delivery_menu(callback: CallbackQuery):
    await callback.message.delete()
    employee = await get_employee(callback.from_user.id)
    if employee:
        await callback.message.answer("Меню доставки", reply_markup=main_menu_keyboard(employee.role))
    await callback.answer()
