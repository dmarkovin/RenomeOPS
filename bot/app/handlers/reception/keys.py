from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter

from app.services.employees.service import get_employee
from app.services.reception.key_service import (
    create_key, get_key, get_keys, return_key,
    add_key_comment, get_key_history
)
from app.database.models import UserRole
from app.keyboards.reception_keys import key_main_menu_keyboard, key_list_keyboard

router = Router()

class KeyCreate(StatesGroup):
    key_number = State()
    recipient = State()
    purpose = State()
    comment = State()
    confirm = State()

class KeyCommentState(StatesGroup):
    waiting_for_comment = State()

# ========== Главное меню ==========
@router.message(F.text == "🔑 Ключи")
async def keys_menu(message: Message, state: FSMContext, page: int = 1, status: str = None):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE):
        await message.answer("У вас нет прав.")
        return

    limit = 10
    offset = (page - 1) * limit
    keys = await get_keys(status=status, limit=limit, offset=offset)
    total = len(keys)
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    if not keys:
        await message.answer("Нет записей.", reply_markup=key_main_menu_keyboard())
        return

    text = "🔑 Список ключей:\n\n"
    for k in keys:
        status_emoji = "🔑" if k.status == "issued" else "✅"
        text += f"{status_emoji} #{k.id} {k.key_number} – {k.recipient} ({k.status})\n"

    sent = await message.answer(text, reply_markup=key_list_keyboard(keys, page, total_pages))
    await state.update_data(key_message_id=sent.message_id, key_chat_id=sent.chat.id, key_status=status)

@router.message(F.text == "📋 Список выданных")
async def list_issued_keys(message: Message, state: FSMContext):
    await keys_menu(message, state, status="issued")

@router.message(F.text == "📋 Возвращённые")
async def list_returned_keys(message: Message, state: FSMContext):
    await keys_menu(message, state, status="returned")

@router.message(F.text == "➕ Выдать ключ")
async def start_create_key(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE):
        await message.answer("Нет прав.")
        return
    await state.clear()
    await state.set_state(KeyCreate.key_number)
    await message.answer("Введите номер ключа:", reply_markup=ReplyKeyboardRemove())

@router.message(KeyCreate.key_number)
async def process_key_number(message: Message, state: FSMContext):
    await state.update_data(key_number=message.text.strip())
    await state.set_state(KeyCreate.recipient)
    await message.answer("Введите ФИО получателя:", reply_markup=ReplyKeyboardRemove())

@router.message(KeyCreate.recipient)
async def process_recipient(message: Message, state: FSMContext):
    await state.update_data(recipient=message.text.strip())
    await state.set_state(KeyCreate.purpose)
    await message.answer("Введите основание (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(KeyCreate.purpose)
async def process_purpose(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(purpose=text if text != "-" else "")
    await state.set_state(KeyCreate.comment)
    await message.answer("Введите комментарий (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(KeyCreate.comment)
async def process_comment(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(comment=text if text != "-" else "")
    await state.set_state(KeyCreate.confirm)
    data = await state.get_data()
    text = (
        f"📝 Проверьте данные:\n\n"
        f"Номер ключа: {data['key_number']}\n"
        f"Получатель: {data['recipient']}\n"
        f"Основание: {data.get('purpose') or '—'}\n"
        f"Комментарий: {data.get('comment') or '—'}\n\n"
        f"Подтвердить выдачу?"
    )
    await message.answer(text, reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Да, выдать")], [KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))

@router.message(KeyCreate.confirm, F.text == "✅ Да, выдать")
async def confirm_create_key(message: Message, state: FSMContext):
    data = await state.get_data()
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка.")
        await state.clear()
        return
    try:
        key = await create_key(
            key_number=data['key_number'],
            recipient=data['recipient'],
            purpose=data.get('purpose'),
            comment=data.get('comment'),
            created_by=employee.id
        )
        await state.clear()
        await message.answer(f"✅ Ключ #{key.id} выдан.", reply_markup=key_main_menu_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", parse_mode=None)
        await state.clear()

@router.message(KeyCreate.confirm, F.text == "❌ Отмена")
async def cancel_create_key(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено", reply_markup=key_main_menu_keyboard())

# ========== Карточка ключа ==========
@router.callback_query(F.data.startswith("key:"))
async def show_key_card(callback: CallbackQuery):
    key_id = int(callback.data.split(":")[1])
    k = await get_key(key_id)
    if not k:
        await callback.answer("Не найден", show_alert=True)
        return
    text = (
        f"🔑 Ключ #{k.id}\n"
        f"Номер: {k.key_number}\n"
        f"Получатель: {k.recipient}\n"
        f"Основание: {k.purpose or '—'}\n"
        f"Выдан: {k.issued_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"Возвращён: {k.returned_at.strftime('%d.%m.%Y %H:%M') if k.returned_at else '—'}\n"
        f"Статус: {k.status}\n"
        f"Комментарий: {k.comment or '—'}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Комментарии", callback_data=f"key_comment_menu:{key_id}")],
        [InlineKeyboardButton(text="📜 История", callback_data=f"key_history:{key_id}")],
    ])
    if k.status == "issued":
        kb.inline_keyboard.append([InlineKeyboardButton(text="✅ Вернуть", callback_data=f"key_return:{key_id}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="key_back")])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("key_return:"))
async def key_return(callback: CallbackQuery):
    key_id = int(callback.data.split(":")[1])
    k = await return_key(key_id)
    if k:
        await callback.answer("✅ Ключ возвращён")
        await show_key_card(callback)
    else:
        await callback.answer("Ошибка", show_alert=True)

# ========== Комментарии ==========
@router.callback_query(F.data.startswith("key_comment_menu:"))
async def key_comment_menu(callback: CallbackQuery):
    key_id = int(callback.data.split(":")[1])
    await callback.message.delete()
    await callback.message.answer(
        "💬 Меню комментариев:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Посмотреть комментарии", callback_data=f"key_comment_list:{key_id}")],
            [InlineKeyboardButton(text="✏️ Добавить комментарий", callback_data=f"key_comment_add:{key_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"key_comment_back:{key_id}")],
        ])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("key_comment_list:"))
async def key_comment_list(callback: CallbackQuery):
    key_id = int(callback.data.split(":")[1])
    k = await get_key(key_id)
    if not k:
        await callback.answer("Не найден", show_alert=True)
        return
    comments = k.comments or []
    if not comments:
        text = "💬 Комментариев пока нет."
    else:
        text = f"💬 <b>Комментарии к ключу #{key_id}</b>\n\n"
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
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data=f"key_comment_menu:{key_id}")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("key_comment_add:"))
async def key_comment_add(callback: CallbackQuery, state: FSMContext):
    key_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    await state.set_state(KeyCommentState.waiting_for_comment)
    await state.update_data(key_id=key_id)
    await callback.message.delete()
    await callback.message.answer("✍️ Введите текст комментария:")
    await callback.answer()

@router.message(StateFilter(KeyCommentState.waiting_for_comment), F.text)
async def key_comment_process(message: Message, state: FSMContext):
    data = await state.get_data()
    key_id = data.get("key_id")
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка")
        await state.clear()
        return
    comment = await add_key_comment(key_id, employee.id, employee.full_name, message.text)
    if comment:
        await message.answer("✅ Комментарий добавлен.")
    else:
        await message.answer("❌ Ошибка.")
    await state.clear()
    await message.answer(
        "💬 Меню комментариев:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Посмотреть комментарии", callback_data=f"key_comment_list:{key_id}")],
            [InlineKeyboardButton(text="✏️ Добавить комментарий", callback_data=f"key_comment_add:{key_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"key_comment_back:{key_id}")],
        ])
    )

@router.callback_query(F.data.startswith("key_comment_back:"))
async def key_comment_back(callback: CallbackQuery):
    key_id = int(callback.data.split(":")[1])
    await callback.message.delete()
    await show_key_card(callback)
    await callback.answer()

# ========== История ==========
@router.callback_query(F.data.startswith("key_history:"))
async def key_history(callback: CallbackQuery):
    key_id = int(callback.data.split(":")[1])
    history = await get_key_history(key_id)
    if not history:
        await callback.answer("История пуста", show_alert=True)
        return
    text = f"📜 <b>История ключа #{key_id}</b>\n\n"
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
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"key:{key_id}")]
        ])
    )
    await callback.answer()

# ========== Пагинация ==========
@router.callback_query(F.data.startswith("key_page:"))
async def paginate_keys(callback: CallbackQuery, state: FSMContext, bot):
    page = int(callback.data.split(":")[1])
    data = await state.get_data()
    message_id = data.get('key_message_id')
    chat_id = data.get('key_chat_id')
    status = data.get('key_status')
    if not message_id or not chat_id:
        message_id = callback.message.message_id
        chat_id = callback.message.chat.id

    limit = 10
    offset = (page - 1) * limit
    keys = await get_keys(status=status, limit=limit, offset=offset)
    total = len(keys)
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    if not keys:
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Нет записей.")
        await callback.answer()
        return

    text = "🔑 Список ключей:\n\n"
    for k in keys:
        status_emoji = "🔑" if k.status == "issued" else "✅"
        text += f"{status_emoji} #{k.id} {k.key_number} – {k.recipient} ({k.status})\n"

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=key_list_keyboard(keys, page, total_pages)
    )
    await callback.answer()

# ========== Назад ==========
@router.callback_query(F.data == "key_back")
async def key_back(callback: CallbackQuery):
    await callback.message.delete()
    employee = await get_employee(callback.from_user.id)
    await callback.message.answer("🔑 Меню ключей:", reply_markup=key_main_menu_keyboard())
    await callback.answer()
