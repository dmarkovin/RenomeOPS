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
import logging

logger = logging.getLogger(__name__)
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

async def safe_delete_message(message):
    try:
        await message.delete()
    except Exception:
        pass

async def safe_edit_or_reply(callback: CallbackQuery, text: str, reply_markup=None, parse_mode="HTML"):
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        await safe_delete_message(callback.message)
        await callback.message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)

@router.message(F.text == "Доставка")
async def reception_menu(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    await message.answer("📦 Меню доставки:", reply_markup=reception_menu_keyboard())

# ========== Создание посылки ==========
@router.message(F.text == "📦 Новая посылка")
async def start_delivery(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
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
        await message.answer("Вы не зарегистрированы.")
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

# ========== Список активных посылок ==========
@router.message(F.text == "📋 Список посылок")
async def list_active_deliveries(message: Message, state: FSMContext, page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    await show_delivery_list(message, state, status=["pending", "received"], title="📦 Активные посылки", page=page)

# ========== Архив доставок ==========
@router.message(F.text == "📦 Архив доставки")
async def list_completed_deliveries(message: Message, state: FSMContext, page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    await show_delivery_list(message, state, status="completed", title="📦 Архив доставок", page=page)

async def show_delivery_list(message: Message, state: FSMContext, status=None, title="Посылки", page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    limit = 10
    offset = (page - 1) * limit
    deliveries = await get_all_deliveries(status=status, limit=limit, offset=offset)
    total = len(deliveries)
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    if not deliveries:
        await message.answer(f"{title}\n\nНет записей.", reply_markup=reception_menu_keyboard())
        return

    text = f"{title} (стр. {page}/{total_pages}):\n\n"
    for d in deliveries:
        status_emoji = {"pending": "🟡", "received": "🔵", "completed": "✅"}.get(d.status, "⚪")
        text += f"{status_emoji} #{d.id} {d.recipient} – кв.{d.apartment} ({d.status})\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for d in deliveries[:10]:
        kb.inline_keyboard.append([InlineKeyboardButton(
            text=f"📦 #{d.id} {d.recipient[:20]} (кв.{d.apartment})",
            callback_data=f"delivery:{d.id}"
        )])
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"delivery_page:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"delivery_page:{page+1}"))
    if nav:
        kb.inline_keyboard.append(nav)
    kb.inline_keyboard.append([InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="delivery_back_to_menu")])

    await state.update_data(delivery_list_status=status, delivery_list_page=page)
    sent = await message.answer(text, reply_markup=kb)
    await state.update_data(delivery_message_id=sent.message_id, delivery_chat_id=sent.chat.id)

@router.callback_query(F.data.startswith("delivery_page:"))
async def paginate_deliveries(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[1])
    data = await state.get_data()
    status = data.get('delivery_list_status')
    await show_delivery_list(callback.message, state, status=status, page=page)
    await callback.answer()

@router.callback_query(F.data == "delivery_back_to_menu")
async def delivery_back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    employee = await get_employee(callback.from_user.id)
    if employee:
        await callback.message.answer("📦 Меню доставки:", reply_markup=reception_menu_keyboard())
    else:
        await callback.answer("Вы не зарегистрированы", show_alert=True)
    await callback.answer()

@router.callback_query(F.data == "delivery_back_to_list")
async def delivery_back_to_list(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    status = data.get('delivery_list_status')
    page = data.get('delivery_list_page', 1)
    await callback.message.delete()
    await show_delivery_list(callback.message, state, status=status, page=page)

# ========== Карточка посылки ==========
@router.callback_query(F.data.startswith("delivery:"))
async def show_delivery_card(callback: CallbackQuery):
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Вы не зарегистрированы", show_alert=True)
        return
    delivery_id = int(callback.data.split(":")[1])
    d = await get_delivery(delivery_id)
    if not d:
        await callback.answer("Не найдена", show_alert=True)
        return
    text = (
        f"📦 Посылка #{d.id}\n"
        f"Получатель: {d.recipient}\n"
        f"Квартира: {d.apartment or '—'}\n"
        f"Курьер: {d.courier_service or '—'}\n"
        f"Статус: {d.status}\n"
        f"Комментарий: {d.comment or '—'}\n"
        f"Создана: {d.created_at.strftime('%d.%m.%Y %H:%M')}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    if d.status == "pending":
        kb.inline_keyboard.append([InlineKeyboardButton(text="📥 Получено", callback_data=f"delivery_receive:{d.id}")])
    if d.status == "received":
        kb.inline_keyboard.append([InlineKeyboardButton(text="✅ Завершить", callback_data=f"delivery_complete:{d.id}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="💬 Комментарии", callback_data=f"delivery_comment_menu:{d.id}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="📜 История", callback_data=f"delivery_history:{d.id}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="delivery_back_to_list")])
    await safe_edit_or_reply(callback, text, kb)
    await callback.answer()

@router.callback_query(F.data.startswith("delivery_receive:"))
async def delivery_receive(callback: CallbackQuery):
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Вы не зарегистрированы", show_alert=True)
        return
    delivery_id = int(callback.data.split(":")[1])
    d = await update_delivery_status(delivery_id, "received")
    if d:
        await callback.answer("✅ Посылка отмечена как полученная")
        await show_delivery_card(callback)
    else:
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("delivery_complete:"))
async def delivery_complete(callback: CallbackQuery):
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Вы не зарегистрированы", show_alert=True)
        return
    delivery_id = int(callback.data.split(":")[1])
    d = await update_delivery_status(delivery_id, "completed")
    if d:
        await callback.answer("✅ Посылка завершена")
        await show_delivery_card(callback)
    else:
        await callback.answer("Ошибка", show_alert=True)

# ========== Комментарии ==========
@router.callback_query(F.data.startswith("delivery_comment_menu:"))
async def delivery_comment_menu(callback: CallbackQuery):
    delivery_id = int(callback.data.split(":")[1])
    await callback.message.delete()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Посмотреть комментарии", callback_data=f"delivery_comment_list:{delivery_id}")],
        [InlineKeyboardButton(text="✏️ Добавить комментарий", callback_data=f"delivery_comment_add:{delivery_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"delivery_comment_back:{delivery_id}")]
    ])
    await callback.message.answer("💬 Меню комментариев:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("delivery_comment_list:"))
async def delivery_comment_list(callback: CallbackQuery):
    delivery_id = int(callback.data.split(":")[1])
    d = await get_delivery(delivery_id)
    if not d:
        await callback.answer("Не найдена", show_alert=True)
        return
    comments = d.comments or []
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
        await callback.answer("Вы не зарегистрированы", show_alert=True)
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
        await message.answer("Вы не зарегистрированы")
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
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"delivery_comment_back:{delivery_id}")]
        ])
    )

@router.callback_query(F.data.startswith("delivery_comment_back:"))
async def delivery_comment_back(callback: CallbackQuery):
    delivery_id = int(callback.data.split(":")[1])
    await callback.message.delete()
    await show_delivery_card(callback)
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

# ========== Обработчик для кнопки "Назад" из меню ==========
@router.message(F.text == "⬅️ Назад" and F.chat.type == "private")
async def back_from_deliveries(message: Message, state: FSMContext):
    await state.clear()
    employee = await get_employee(message.from_user.id)
    if employee:
        from app.keyboards.main_menu import main_menu_keyboard
        await message.answer("Главное меню:", reply_markup=main_menu_keyboard(employee.role))
    else:
        await message.answer("Возврат...")
