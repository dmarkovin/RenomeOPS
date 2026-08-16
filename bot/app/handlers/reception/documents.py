from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter

from app.services.employees.service import get_employee
from app.services.reception.document_service import (
    create_document, get_document, get_documents,
    update_document_status, delete_document,
    add_document_comment, get_document_history
)
from app.database.models import UserRole
from app.keyboards.reception_documents import (
    doc_list_keyboard, doc_action_keyboard, doc_main_menu_keyboard
)
from app.keyboards.main_menu import main_menu_keyboard
from app.permissions import has_permission, Permission

router = Router()

class DocumentCreate(StatesGroup):
    name = State()
    doc_type = State()
    number = State()
    sender = State()
    recipient = State()
    comment = State()
    photo = State()
    confirm = State()

class DocumentCommentState(StatesGroup):
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

# ========== Главное меню документов ==========
@router.message(F.text == "📄 Документы")
async def documents_menu(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee or not has_permission(employee, Permission.DOCUMENTS_MANAGE):
        await message.answer("У вас нет прав.")
        return
    await state.clear()
    await message.answer("📄 Управление документами:", reply_markup=doc_main_menu_keyboard())

# ========== Создание документа ==========
@router.message(F.text == "➕ Новый документ")
async def start_create_document(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee or not has_permission(employee, Permission.DOCUMENTS_MANAGE):
        await message.answer("Нет прав.")
        return
    await state.clear()
    await state.set_state(DocumentCreate.name)
    await message.answer("Введите название документа:", reply_markup=ReplyKeyboardRemove())

@router.message(DocumentCreate.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📥 Входящий")],
            [types.KeyboardButton(text="📤 Исходящий")],
            [types.KeyboardButton(text="📦 На хранение")],
            [types.KeyboardButton(text="📋 Выданный")],
            [types.KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    await state.set_state(DocumentCreate.doc_type)
    await message.answer("Выберите тип документа:", reply_markup=kb)

@router.message(StateFilter(DocumentCreate.doc_type), F.text.in_(["📥 Входящий", "📤 Исходящий", "📦 На хранение", "📋 Выданный"]))
async def process_type(message: Message, state: FSMContext):
    type_map = {
        "📥 Входящий": "incoming",
        "📤 Исходящий": "outgoing",
        "📦 На хранение": "storage",
        "📋 Выданный": "issued",
    }
    await state.update_data(doc_type=type_map[message.text])
    await state.set_state(DocumentCreate.number)
    await message.answer("Введите номер документа (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(StateFilter(DocumentCreate.doc_type), F.text == "❌ Отмена")
async def cancel_create(message: Message, state: FSMContext):
    await state.clear()
    employee = await get_employee(message.from_user.id)
    await message.answer("Создание отменено", reply_markup=doc_main_menu_keyboard())

@router.message(StateFilter(DocumentCreate.doc_type))
async def invalid_type(message: Message):
    await message.answer("Пожалуйста, выберите тип кнопкой.")

@router.message(DocumentCreate.number)
async def process_number(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(number=text if text != "-" else "")
    await state.set_state(DocumentCreate.sender)
    await message.answer("Введите отправителя (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(DocumentCreate.sender)
async def process_sender(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(sender=text if text != "-" else "")
    await state.set_state(DocumentCreate.recipient)
    await message.answer("Введите получателя (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(DocumentCreate.recipient)
async def process_recipient(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(recipient=text if text != "-" else "")
    await state.set_state(DocumentCreate.comment)
    await message.answer("Введите комментарий (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(DocumentCreate.comment)
async def process_comment(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(comment=text if text != "-" else "")
    await state.set_state(DocumentCreate.photo)
    await message.answer("🖼 Пришлите фото (опционально) или нажмите **Готово**:", reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="✅ Готово")], [types.KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))

@router.message(StateFilter(DocumentCreate.photo), F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Добавлено фото ({len(photos)})")

@router.message(StateFilter(DocumentCreate.photo), F.text == "✅ Готово")
async def finish_photo(message: Message, state: FSMContext):
    await state.set_state(DocumentCreate.confirm)
    data = await state.get_data()
    text = (
        f"📝 Проверьте данные документа:\n\n"
        f"Название: {data['name']}\n"
        f"Тип: {data['doc_type']}\n"
        f"Номер: {data.get('number') or '—'}\n"
        f"Отправитель: {data.get('sender') or '—'}\n"
        f"Получатель: {data.get('recipient') or '—'}\n"
        f"Комментарий: {data.get('comment') or '—'}\n"
        f"Фото: {len(data.get('photos', []))} шт.\n\n"
        f"Подтвердить создание?"
    )
    await message.answer(text, reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="✅ Да, создать")],
            [types.KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    ))

@router.message(StateFilter(DocumentCreate.photo), F.text == "❌ Отмена")
async def cancel_photo(message: Message, state: FSMContext):
    await state.clear()
    employee = await get_employee(message.from_user.id)
    await message.answer("Создание отменено", reply_markup=doc_main_menu_keyboard())

@router.message(DocumentCreate.confirm, F.text == "✅ Да, создать")
async def confirm_create(message: Message, state: FSMContext):
    data = await state.get_data()
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка.")
        await state.clear()
        return
    try:
        doc = await create_document(
            name=data['name'],
            doc_type=data['doc_type'],
            number=data.get('number'),
            sender=data.get('sender'),
            recipient=data.get('recipient'),
            comment=data.get('comment'),
            photo_ids=data.get('photos', []),
            created_by=employee.id
        )
        await state.clear()
        await message.answer(f"✅ Документ #{doc.id} создан.", reply_markup=doc_main_menu_keyboard())
        await message.answer("Выберите действие:", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", parse_mode=None)
        await state.clear()

@router.message(DocumentCreate.confirm, F.text == "❌ Отмена")
async def cancel_create(message: Message, state: FSMContext):
    await state.clear()
    employee = await get_employee(message.from_user.id)
    await message.answer("Отменено", reply_markup=doc_main_menu_keyboard())

# ========== Списки документов ==========
@router.message(F.text == "📋 Входящие")
async def list_incoming(message: Message, state: FSMContext, page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee or not has_permission(employee, Permission.DOCUMENTS_MANAGE):
        await message.answer("Нет прав.")
        return
    await show_doc_list(message, state, doc_type="incoming", title="📥 Входящие документы", page=page)

@router.message(F.text == "📋 Исходящие")
async def list_outgoing(message: Message, state: FSMContext, page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee or not has_permission(employee, Permission.DOCUMENTS_MANAGE):
        await message.answer("Нет прав.")
        return
    await show_doc_list(message, state, doc_type="outgoing", title="📤 Исходящие документы", page=page)

@router.message(F.text == "📋 На хранении")
async def list_storage(message: Message, state: FSMContext, page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee or not has_permission(employee, Permission.DOCUMENTS_MANAGE):
        await message.answer("Нет прав.")
        return
    await show_doc_list(message, state, doc_type="storage", status="active", title="📦 На хранении", page=page)

@router.message(F.text == "📋 Выданные")
async def list_issued(message: Message, state: FSMContext, page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee or not has_permission(employee, Permission.DOCUMENTS_MANAGE):
        await message.answer("Нет прав.")
        return
    await show_doc_list(message, state, doc_type="issued", status="active", title="📋 Выданные", page=page)

async def show_doc_list(message: Message, state: FSMContext, doc_type: str = None, status: str = None, title: str = "Документы", page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee or not has_permission(employee, Permission.DOCUMENTS_MANAGE):
        await message.answer("Нет прав.")
        return
    limit = 10
    offset = (page - 1) * limit
    docs = await get_documents(doc_type=doc_type, status=status, limit=limit, offset=offset)
    total = len(docs)
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    if not docs:
        await message.answer(f"{title}\n\nНет документов.", reply_markup=doc_main_menu_keyboard())
        return

    text = f"{title} (стр. {page}/{total_pages}):\n\n"
    for d in docs:
        type_emoji = {"incoming": "📥", "outgoing": "📤", "storage": "📦", "issued": "📋"}.get(d.doc_type, "📄")
        text += f"{type_emoji} #{d.id} {d.name} ({d.doc_type})\n"

    sent = await message.answer(text, reply_markup=doc_list_keyboard(docs, page, total_pages))
    await state.update_data(doc_type=doc_type, doc_status=status, doc_message_id=sent.message_id, doc_chat_id=sent.chat.id, doc_page=page)

@router.callback_query(F.data.startswith("doc_page:"))
async def paginate_docs(callback: CallbackQuery, state: FSMContext, bot):
    page = int(callback.data.split(":")[1])
    data = await state.get_data()
    doc_type = data.get('doc_type')
    doc_status = data.get('doc_status')
    message_id = data.get('doc_message_id')
    chat_id = data.get('doc_chat_id')
    if not message_id or not chat_id:
        message_id = callback.message.message_id
        chat_id = callback.message.chat.id

    limit = 10
    offset = (page - 1) * limit
    docs = await get_documents(doc_type=doc_type, status=doc_status, limit=limit, offset=offset)
    total = len(docs)
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    if not docs:
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="Нет документов.")
        await callback.answer()
        return

    title = doc_type.capitalize() if doc_type else "Документы"
    text = f"{title} (стр. {page}/{total_pages}):\n\n"
    for d in docs:
        type_emoji = {"incoming": "📥", "outgoing": "📤", "storage": "📦", "issued": "📋"}.get(d.doc_type, "📄")
        text += f"{type_emoji} #{d.id} {d.name} ({d.doc_type})\n"

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=doc_list_keyboard(docs, page, total_pages)
    )
    await callback.answer()
    await state.update_data(doc_page=page)

# ========== Карточка документа ==========
@router.callback_query(F.data.startswith("doc:"))
async def show_doc_card(callback: CallbackQuery):
    employee = await get_employee(callback.from_user.id)
    if not employee or not has_permission(employee, Permission.DOCUMENTS_MANAGE):
        await callback.answer("У вас нет прав", show_alert=True)
        return
    doc_id = int(callback.data.split(":")[1])
    d = await get_document(doc_id)
    if not d:
        await callback.answer("Не найден", show_alert=True)
        return
    text = (
        f"📄 Документ #{d.id}\n"
        f"Название: {d.name}\n"
        f"Тип: {d.doc_type}\n"
        f"Номер: {d.number or '—'}\n"
        f"Отправитель: {d.sender or '—'}\n"
        f"Получатель: {d.recipient or '—'}\n"
        f"Статус: {d.status}\n"
        f"Комментарий: {d.comment or '—'}\n"
        f"Создан: {d.created_at.strftime('%d.%m.%Y %H:%M')}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    if d.status == "active" and d.doc_type in ("storage", "issued"):
        kb.inline_keyboard.append([InlineKeyboardButton(text="✅ Отметить возврат", callback_data=f"doc_return:{d.id}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="💬 Комментарии", callback_data=f"doc_comment_menu:{d.id}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="📜 История", callback_data=f"doc_history:{d.id}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="doc_back_to_list")])
    await safe_edit_or_reply(callback, text, kb)
    await callback.answer()

@router.callback_query(F.data == "doc_back_to_list")
async def doc_back_to_list(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    doc_type = data.get('doc_type')
    doc_status = data.get('doc_status')
    page = data.get('doc_page', 1)
    await callback.message.delete()
    employee = await get_employee(callback.from_user.id)
    if employee and has_permission(employee, Permission.DOCUMENTS_MANAGE):
        await show_doc_list(callback.message, state, doc_type=doc_type, status=doc_status, page=page)
    await callback.answer()

@router.callback_query(F.data.startswith("doc_return:"))
async def doc_return(callback: CallbackQuery):
    doc_id = int(callback.data.split(":")[1])
    d = await update_document_status(doc_id, "returned")
    if d:
        await callback.answer("✅ Возврат отмечен")
        await show_doc_card(callback)
    else:
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data == "doc_back_to_menu")
async def back_to_doc_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    employee = await get_employee(callback.from_user.id)
    if employee and has_permission(employee, Permission.DOCUMENTS_MANAGE):
        await callback.message.answer("📄 Управление документами:", reply_markup=doc_main_menu_keyboard())
    await callback.answer()

# ========== Комментарии ==========
@router.callback_query(F.data.startswith("doc_comment_menu:"))
async def doc_comment_menu(callback: CallbackQuery):
    doc_id = int(callback.data.split(":")[1])
    await callback.message.delete()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Посмотреть комментарии", callback_data=f"doc_comment_list:{doc_id}")],
        [InlineKeyboardButton(text="✏️ Добавить комментарий", callback_data=f"doc_comment_add:{doc_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"doc_comment_back:{doc_id}")]
    ])
    await callback.message.answer("💬 Меню комментариев:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("doc_comment_list:"))
async def doc_comment_list(callback: CallbackQuery):
    doc_id = int(callback.data.split(":")[1])
    d = await get_document(doc_id)
    if not d:
        await callback.answer("Не найден", show_alert=True)
        return
    comments = d.comments or []
    if not comments:
        text = "💬 Комментариев пока нет."
    else:
        text = f"💬 <b>Комментарии к документу #{doc_id}</b>\n\n"
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
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data=f"doc_comment_menu:{doc_id}")]
        ])
    )
    await callback.answer()

@router.callback_query(F.data.startswith("doc_comment_add:"))
async def doc_comment_add(callback: CallbackQuery, state: FSMContext):
    doc_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    await state.set_state(DocumentCommentState.waiting_for_comment)
    await state.update_data(doc_id=doc_id)
    await callback.message.delete()
    await callback.message.answer("✍️ Введите текст комментария:")
    await callback.answer()

@router.message(StateFilter(DocumentCommentState.waiting_for_comment), F.text)
async def doc_comment_process(message: Message, state: FSMContext):
    data = await state.get_data()
    doc_id = data.get("doc_id")
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка")
        await state.clear()
        return
    comment = await add_document_comment(doc_id, employee.id, employee.full_name, message.text)
    if comment:
        await message.answer("✅ Комментарий добавлен.")
    else:
        await message.answer("❌ Ошибка.")
    await state.clear()
    await message.answer(
        "💬 Меню комментариев:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Посмотреть комментарии", callback_data=f"doc_comment_list:{doc_id}")],
            [InlineKeyboardButton(text="✏️ Добавить комментарий", callback_data=f"doc_comment_add:{doc_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"doc_comment_back:{doc_id}")]
        ])
    )

@router.callback_query(F.data.startswith("doc_comment_back:"))
async def doc_comment_back(callback: CallbackQuery):
    doc_id = int(callback.data.split(":")[1])
    await callback.message.delete()
    await show_doc_card(callback)
    await callback.answer()

# ========== История ==========
@router.callback_query(F.data.startswith("doc_history:"))
async def doc_history(callback: CallbackQuery):
    doc_id = int(callback.data.split(":")[1])
    history = await get_document_history(doc_id)
    if not history:
        await callback.answer("История пуста", show_alert=True)
        return
    text = f"📜 <b>История документа #{doc_id}</b>\n\n"
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
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"doc:{doc_id}")]
        ])
    )
    await callback.answer()

# ========== Обработчик для кнопки "Назад" из меню ==========
@router.message(F.text == "⬅️ Назад" and F.chat.type == "private")
async def back_from_documents(message: Message, state: FSMContext):
    await state.clear()
    employee = await get_employee(message.from_user.id)
    if employee:
        from app.keyboards.main_menu import main_menu_keyboard
        await message.answer("Главное меню:", reply_markup=main_menu_keyboard(employee.role))
    else:
        await message.answer("Возврат...")
