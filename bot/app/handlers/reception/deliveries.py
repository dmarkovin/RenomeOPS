from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter

from app.services.employees.service import get_employee
from app.services.reception.delivery_service import (
    create_delivery, get_all_deliveries, get_delivery,
    update_delivery_status, add_delivery_comment, get_delivery_history
)
from app.database.models import UserRole
from app.keyboards.reception import reception_menu_keyboard

router = Router()

class DeliveryCreate(StatesGroup):
    recipient = State()
    apartment = State()
    courier = State()
    comment = State()
    photo = State()
    confirm = State()

class DeliveryCommentState(StatesGroup):
    waiting_for_comment = State()

# ========== Главное меню ==========
@router.message(F.text == "📦 Доставка")
async def reception_menu(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE):
        await message.answer("У вас нет прав.")
        return
    await message.answer("📦 Меню доставки:", reply_markup=reception_menu_keyboard())

# ========== Создание посылки ==========
@router.message(F.text == "📦 Посылка")
async def start_delivery(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка")
        return
    await state.clear()
    await state.set_state(DeliveryCreate.recipient)
    await message.answer("Введите ФИО получателя:", reply_markup=ReplyKeyboardRemove())

@router.message(DeliveryCreate.recipient)
async def delivery_recipient(message: Message, state: FSMContext):
    await state.update_data(recipient=message.text.strip())
    await state.set_state(DeliveryCreate.apartment)
    await message.answer("Введите номер квартиры (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(DeliveryCreate.apartment)
async def delivery_apartment(message: Message, state: FSMContext):
    text = message.text.strip()
    apartment = int(text) if text.isdigit() else None
    await state.update_data(apartment=apartment)
    await state.set_state(DeliveryCreate.courier)
    await message.answer("Введите название курьерской службы (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(DeliveryCreate.courier)
async def delivery_courier(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(courier=text if text != "-" else "")
    await state.set_state(DeliveryCreate.comment)
    await message.answer("Введите комментарий (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(DeliveryCreate.comment)
async def delivery_comment(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(comment=text if text != "-" else "")
    await state.set_state(DeliveryCreate.photo)
    await message.answer("🖼 Пришлите фото (опционально) или нажмите **Готово**:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Готово")]],
        resize_keyboard=True
    ))

@router.message(DeliveryCreate.photo, F.photo)
async def delivery_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Добавлено фото ({len(photos)})")

@router.message(DeliveryCreate.photo, F.text == "✅ Готово")
async def delivery_ready(message: Message, state: FSMContext):
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
    await message.answer(text, reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Да, создать")], [KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))

@router.message(DeliveryCreate.confirm, F.text == "✅ Да, создать")
async def delivery_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка.")
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
        await message.answer(f"✅ Посылка #{delivery.id} создана!", reply_markup=reception_menu_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", parse_mode=None)
        await state.clear()

@router.message(DeliveryCreate.confirm, F.text == "❌ Отмена")
async def delivery_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено", reply_markup=reception_menu_keyboard())

# ========== Список посылок (активные) ==========
@router.message(F.text == "📋 Список посылок")
async def list_active_deliveries(message: Message, state: FSMContext, page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE):
        await message.answer("Нет прав.")
        return
    limit = 10
    offset = (page - 1) * limit
    all_active = await get_all_deliveries(status=None, limit=10000, offset=0)  # получим все
    active_deliveries = [d for d in all_active if d.status in ("pending", "received")]
    total = len(active_deliveries)
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    start = (page - 1) * limit
    deliveries_page = active_deliveries[start:start+limit]

    if not deliveries_page:
        await message.answer("Нет активных посылок.")
        return

    text = f"📦 Список посылок (стр. {page}/{total_pages}):\n\n"
    for d in deliveries_page:
        status_emoji = "🟡" if d.status == "pending" else "🔵"
        text += f"{status_emoji} #{d.id} {d.recipient} ({d.status})\n"

    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"delivery_page:{page-1}"))
    buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"delivery_page:{page+1}"))
    kb = InlineKeyboardMarkup(inline_keyboard=[buttons]) if buttons else None

    # Добавим кнопки для каждой посылки
    for d in deliveries_page:
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"#{d.id} {d.recipient}", callback_data=f"delivery:{d.id}")])

    await state.update_data(delivery_list_page=page)
    sent = await message.answer(text, reply_markup=kb)
    await state.update_data(delivery_message_id=sent.message_id, delivery_chat_id=sent.chat.id)

# ========== Пагинация списка посылок ==========
@router.callback_query(F.data.startswith("delivery_page:"))
async def paginate_deliveries(callback: CallbackQuery, state: FSMContext, bot):
    page = int(callback.data.split(":")[1])
    data = await state.get_data()
    message_id = data.get('delivery_message_id')
    chat_id = data.get('delivery_chat_id')
    if not message_id or not chat_id:
        message_id = callback.message.message_id
        chat_id = callback.message.chat.id

    # Перезагружаем список
    employee = await get_employee(callback.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE):
        await callback.answer("Нет прав.", show_alert=True)
        return
    limit = 10
    offset = (page - 1) * limit
    all_active = await get_all_deliveries(status=None, limit=10000, offset=0)
    active_deliveries = [d for d in all_active if d.status in ("pending", "received")]
    total = len(active_deliveries)
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    start = (page - 1) * limit
    deliveries_page = active_deliveries[start:start+limit]

    if not deliveries_page:
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Нет активных посылок.")
        await callback.answer()
        return

    text = f"📦 Список посылок (стр. {page}/{total_pages}):\n\n"
    for d in deliveries_page:
        status_emoji = "🟡" if d.status == "pending" else "🔵"
        text += f"{status_emoji} #{d.id} {d.recipient} ({d.status})\n"

    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"delivery_page:{page-1}"))
    buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"delivery_page:{page+1}"))
    kb = InlineKeyboardMarkup(inline_keyboard=[buttons]) if buttons else None
    for d in deliveries_page:
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"#{d.id} {d.recipient}", callback_data=f"delivery:{d.id}")])

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=kb
    )
    await callback.answer()

# ========== Карточка посылки ==========
@router.callback_query(F.data.startswith("delivery:"))
async def show_delivery_card(callback: CallbackQuery):
    delivery_id = int(callback.data.split(":")[1])
    delivery = await get_delivery(delivery_id)
    if not delivery:
        await callback.answer("Не найдено", show_alert=True)
        return
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    status_emoji = {
        "pending": "🟡",
        "received": "🔵",
        "completed": "✅"
    }.get(delivery.status, "⚪")
    text = (
        f"{status_emoji} <b>Посылка #{delivery.id}</b>\n\n"
        f"Получатель: {delivery.recipient}\n"
        f"Квартира: {delivery.apartment or '—'}\n"
        f"Курьер: {delivery.courier_service or '—'}\n"
        f"Статус: {delivery.status}\n"
        f"Комментарий: {delivery.comment or '—'}\n"
        f"Создана: {delivery.created_at.strftime('%d.%m.%Y %H:%M')}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Комментарии", callback_data=f"delivery_comment_menu:{delivery_id}")],
        [InlineKeyboardButton(text="📷 Фото", callback_data=f"delivery_photo:{delivery_id}")],
        [InlineKeyboardButton(text="📜 История", callback_data=f"delivery_history:{delivery_id}")],
    ])
    if delivery.status == "pending":
        kb.inline_keyboard.append([InlineKeyboardButton(text="📥 Получено", callback_data=f"delivery_receive:{delivery_id}")])
    elif delivery.status == "received":
        kb.inline_keyboard.append([InlineKeyboardButton(text="✅ Завершить", callback_data=f"delivery_complete:{delivery_id}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="delivery_back_from_card")])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("delivery_receive:"))
async def delivery_receive(callback: CallbackQuery):
    delivery_id = int(callback.data.split(":")[1])
    delivery = await update_delivery_status(delivery_id, "received")
    if delivery:
        await callback.answer("✅ Отмечено как получено")
        await show_delivery_card(callback)
    else:
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("delivery_complete:"))
async def delivery_complete(callback: CallbackQuery):
    delivery_id = int(callback.data.split(":")[1])
    delivery = await update_delivery_status(delivery_id, "completed")
    if delivery:
        await callback.answer("✅ Завершено")
        await show_delivery_card(callback)
    else:
        await callback.answer("Ошибка", show_alert=True)

# ========== Комментарии ==========
@router.callback_query(F.data.startswith("delivery_comment_menu:"))
async def delivery_comment_menu(callback: CallbackQuery):
    delivery_id = int(callback.data.split(":")[1])
    await callback.message.delete()
    await callback.message.answer(
        "💬 Меню комментариев:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Посмотреть комментарии", callback_data=f"delivery_comment_list:{delivery_id}")],
            [InlineKeyboardButton(text="✏️ Добавить комментарий", callback_data=f"delivery_comment_add:{delivery_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"delivery_comment_back:{delivery_id}")],
        ])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("delivery_comment_list:"))
async def delivery_comment_list(callback: CallbackQuery):
    delivery_id = int(callback.data.split(":")[1])
    delivery = await get_delivery(delivery_id)
    if not delivery:
        await callback.answer("Не найдено", show_alert=True)
        return
    comments = delivery.comments or []
    if not comments:
        text = "💬 Комментариев пока нет."
    else:
        text = f"💬 <b>Комментарии к посылке #{delivery_id}</b>\n\n"
        for c in comments[:10]:
            user_name = c.get("author_name", "—")
            created_at = c.get("created_at", "")
            text += f"👤 {user_name} | {created_at}\n"
            text += f"{c.get('text', '')}\n\n"
    await callback.message.delete()
    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data=f"delivery_comment_menu:{delivery_id}")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("delivery_comment_add:"))
async def delivery_comment_add(callback: CallbackQuery, state: FSMContext):
    delivery_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    await state.set_state(DeliveryCommentState.waiting_for_comment)
    await state.update_data(delivery_id=delivery_id)
    await callback.message.delete()
    await callback.message.answer("✍️ Введите текст комментария:")
    await callback.answer()

@router.message(StateFilter(DeliveryCommentState.waiting_for_comment), F.text)
async def delivery_comment_process(message: Message, state: FSMContext):
    data = await state.get_data()
    delivery_id = data.get("delivery_id")
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка")
        await state.clear()
        return
    comment = await add_delivery_comment(delivery_id, employee.id, employee.full_name, message.text)
    if comment:
        await message.answer("✅ Комментарий добавлен.")
    else:
        await message.answer("❌ Ошибка.")
    await state.clear()
    await message.answer(
        "💬 Меню комментариев:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Посмотреть комментарии", callback_data=f"delivery_comment_list:{delivery_id}")],
            [InlineKeyboardButton(text="✏️ Добавить комментарий", callback_data=f"delivery_comment_add:{delivery_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"delivery_comment_back:{delivery_id}")],
        ])
    )

@router.callback_query(F.data.startswith("delivery_comment_back:"))
async def delivery_comment_back(callback: CallbackQuery):
    delivery_id = int(callback.data.split(":")[1])
    await callback.message.delete()
    await show_delivery_card(callback)
    await callback.answer()

# ========== Фото ==========
@router.callback_query(F.data.startswith("delivery_photo:"))
async def delivery_photo(callback: CallbackQuery):
    delivery_id = int(callback.data.split(":")[1])
    delivery = await get_delivery(delivery_id)
    if not delivery or not delivery.photo_ids:
        await callback.answer("Нет фото", show_alert=True)
        return
    await callback.message.delete()
    for file_id in delivery.photo_ids:
        await callback.message.answer_photo(file_id)
    await callback.message.answer(
        "⬅️ Назад",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"delivery:{delivery_id}")]
        ])
    )
    await callback.answer()

# ========== История ==========
@router.callback_query(F.data.startswith("delivery_history:"))
async def delivery_history(callback: CallbackQuery):
    delivery_id = int(callback.data.split(":")[1])
    history = await get_delivery_history(delivery_id)
    if not history:
        await callback.answer("История пуста", show_alert=True)
        return
    text = f"📜 <b>История посылки #{delivery_id}</b>\n\n"
    for entry in history[:10]:
        text += f"🕒 {entry.get('created_at', '')}\n"
        text += f"👤 {entry.get('author', 'Система')}\n"
        text += f"📌 {entry.get('action', '')}\n"
        text += f"📝 {entry.get('description', '')}\n\n"
    await callback.message.delete()
    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"delivery:{delivery_id}")]
        ])
    )
    await callback.answer()

# ========== Архив доставки ==========
@router.message(F.text == "📦 Архив доставки")
async def delivery_archive(message: Message, page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE):
        await message.answer("Нет прав.")
        return
    limit = 10
    offset = (page - 1) * limit
    deliveries = await get_all_deliveries(status="completed", limit=limit, offset=offset)
    all_completed = await get_all_deliveries(status="completed", limit=10000, offset=0)
    total_count = len(all_completed)
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

    if not deliveries:
        await message.answer("Архив пуст.")
        return

    text = f"📦 Архив посылок (стр. {page}/{total_pages}):\n\n"
    for d in deliveries:
        text += f"#{d.id} {d.recipient} ({d.status})\n"

    kb_buttons = []
    if page > 1:
        kb_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"archive_delivery_page:{page-1}"))
    kb_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        kb_buttons.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"archive_delivery_page:{page+1}"))
    kb = InlineKeyboardMarkup(inline_keyboard=[kb_buttons]) if kb_buttons else None
    await message.answer(text, reply_markup=kb)

@router.callback_query(F.data.startswith("archive_delivery_page:"))
async def archive_delivery_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    await delivery_archive(callback.message, page)
    await callback.answer()

# ========== Назад из карточки ==========
@router.callback_query(F.data == "delivery_back_from_card")
async def delivery_back_from_card(callback: CallbackQuery):
    await callback.message.delete()
    employee = await get_employee(callback.from_user.id)
    if employee and employee.role in (UserRole.ADMIN, UserRole.CONCIERGE):
        await callback.message.answer("📦 Меню доставки:", reply_markup=reception_menu_keyboard())
    await callback.answer()

# ========== Старый назад (для совместимости) ==========
@router.callback_query(F.data == "delivery_back")
async def delivery_back(callback: CallbackQuery):
    await callback.message.delete()
    employee = await get_employee(callback.from_user.id)
    if employee and employee.role in (UserRole.ADMIN, UserRole.CONCIERGE):
        await callback.message.answer("📦 Меню доставки:", reply_markup=reception_menu_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("delivery_receive_from_list:"))
async def delivery_receive_from_list(callback: CallbackQuery):
    delivery_id = int(callback.data.split(":")[1])
    delivery = await update_delivery_status(delivery_id, "received")
    if delivery:
        await callback.answer("✅ Отмечено как получено")
        # Обновляем список
        await list_active_deliveries(callback.message, await callback.bot.get_state(callback.from_user.id), page=1)
    else:
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("delivery_complete_from_list:"))
async def delivery_complete_from_list(callback: CallbackQuery):
    delivery_id = int(callback.data.split(":")[1])
    delivery = await update_delivery_status(delivery_id, "completed")
    if delivery:
        await callback.answer("✅ Завершено")
        await list_active_deliveries(callback.message, await callback.bot.get_state(callback.from_user.id), page=1)
    else:
        await callback.answer("Ошибка", show_alert=True)
