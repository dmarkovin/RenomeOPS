from aiogram.types import ReplyKeyboardRemove
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter

from app.services.employees.service import get_employee
from app.services.reception.document_service import (
    create_document, get_document, get_documents,
    update_document_status, delete_document
)
from app.database.models import UserRole
from app.keyboards.reception_documents import (
    doc_list_keyboard, doc_action_keyboard, doc_main_menu_keyboard
)
from app.keyboards.main_menu import main_menu_keyboard

router = Router()

class DocumentCreate(StatesGroup):
    name = State()
    doc_type = State()
    number = State()
    sender = State()
    recipient = State()
    issued_to = State()
    issued_at = State()
    comment = State()
    photo = State()
    confirm = State()

@router.message(F.text == "📄 Документы")
async def documents_menu(message: Message, state: FSMContext, page: int = 1, doc_type: str = None, status: str = None):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE):
        await message.answer("У вас нет прав.")
        return

    limit = 10
    offset = (page - 1) * limit
    docs = await get_documents(doc_type=doc_type, status=status, limit=limit, offset=offset)
    total = len(docs)
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    if not docs:
        await message.answer("Нет документов.", reply_markup=doc_main_menu_keyboard())
        return

    text = "📋 Список документов:\n\n"
    for d in docs:
        type_emoji = {"incoming": "📥", "outgoing": "📤", "storage": "📦", "issued": "📋"}.get(d.doc_type, "📄")
        text += f"{type_emoji} #{d.id} {d.name} ({d.doc_type})\n"

    sent = await message.answer(text, reply_markup=doc_list_keyboard(docs, page, total_pages))
    await state.update_data(doc_message_id=sent.message_id, doc_chat_id=sent.chat.id, doc_type=doc_type, doc_status=status)

@router.message(F.text == "📋 Входящие")
async def list_incoming(message: Message, state: FSMContext):
    await documents_menu(message, state, doc_type="incoming")

@router.message(F.text == "📋 Исходящие")
async def list_outgoing(message: Message, state: FSMContext):
    await documents_menu(message, state, doc_type="outgoing")

@router.message(F.text == "📋 На хранении")
async def list_storage(message: Message, state: FSMContext):
    await documents_menu(message, state, doc_type="storage", status="active")

@router.message(F.text == "📋 Выданные")
async def list_issued(message: Message, state: FSMContext):
    await documents_menu(message, state, doc_type="issued", status="active")

@router.message(F.text == "➕ Новый документ")
async def start_create_document(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE):
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
        ],
        resize_keyboard=True
    )
    await state.set_state(DocumentCreate.doc_type)
    await message.answer("Выберите тип документа:", reply_markup=kb)

@router.message(DocumentCreate.doc_type)
async def process_type(message: Message, state: FSMContext):
    type_map = {
        "📥 Входящий": "incoming",
        "📤 Исходящий": "outgoing",
        "📦 На хранение": "storage",
        "📋 Выданный": "issued",
    }
    if message.text not in type_map:
        await message.answer("Пожалуйста, выберите тип кнопкой.")
        return
    await state.update_data(doc_type=type_map[message.text])
    await state.set_state(DocumentCreate.number)
    await message.answer("Введите номер документа (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

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
    await state.set_state(DocumentCreate.issued_to)
    await message.answer("Введите кому выдан (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(DocumentCreate.issued_to)
async def process_issued_to(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(issued_to=text if text != "-" else "")
    await state.set_state(DocumentCreate.issued_at)
    await message.answer("Введите дату выдачи (ДД.ММ.ГГГГ) или '-' для сегодня:", reply_markup=ReplyKeyboardRemove())

@router.message(DocumentCreate.issued_at)
async def process_issued_at(message: Message, state: FSMContext):
    from datetime import datetime
    text = message.text.strip()
    if text == "-":
        issued_at = datetime.now()
    else:
        try:
            issued_at = datetime.strptime(text, "%d.%m.%Y")
        except:
            await message.answer("Неверный формат. Используйте ДД.ММ.ГГГГ или '-'.")
            return
    await state.update_data(issued_at=issued_at)
    await state.set_state(DocumentCreate.comment)
    await message.answer("Введите комментарий (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(DocumentCreate.comment)
async def process_comment(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(comment=text if text != "-" else "")
    await state.set_state(DocumentCreate.photo)
    await message.answer("🖼 Пришлите фото (опционально) или нажмите **Готово**:", reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="✅ Готово")]],
        resize_keyboard=True
    ))

@router.message(DocumentCreate.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Добавлено фото ({len(photos)})")

@router.message(DocumentCreate.photo, F.text == "✅ Готово")
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
        f"Выдан: {data.get('issued_to') or '—'}\n"
        f"Дата выдачи: {data.get('issued_at').strftime('%d.%m.%Y')}\n"
        f"Комментарий: {data.get('comment') or '—'}\n"
        f"Фото: {len(data.get('photos', []))} шт.\n\n"
        f"Подтвердить создание?"
    )
    await message.answer(text, reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="✅ Да, создать")], [types.KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))

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
            issued_to=data.get('issued_to'),
            issued_at=data.get('issued_at'),
            comment=data.get('comment'),
            photo_ids=data.get('photos', []),
            created_by=employee.id
        )
        await state.clear()
        await message.answer(f"✅ Документ #{doc.id} создан.", reply_markup=doc_main_menu_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", parse_mode=None)
        await state.clear()

@router.message(DocumentCreate.confirm, F.text == "❌ Отмена")
async def cancel_create(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено", reply_markup=doc_main_menu_keyboard())

# Карточка документа
@router.callback_query(F.data.startswith("doc:"))
async def show_doc_card(callback: CallbackQuery):
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
        f"Выдан: {d.issued_to or '—'}\n"
        f"Дата выдачи: {d.issued_at.strftime('%d.%m.%Y') if d.issued_at else '—'}\n"
        f"Возврат: {d.returned_at.strftime('%d.%m.%Y') if d.returned_at else '—'}\n"
        f"Статус: {d.status}\n"
        f"Комментарий: {d.comment or '—'}"
    )
    await callback.message.edit_text(text, reply_markup=doc_action_keyboard(d.id, d.status))
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

@router.callback_query(F.data.startswith("doc_page:"))
async def paginate_docs(callback: CallbackQuery, state: FSMContext, bot):
    page = int(callback.data.split(":")[1])
    data = await state.get_data()
    message_id = data.get('doc_message_id')
    chat_id = data.get('doc_chat_id')
    doc_type = data.get('doc_type')
    doc_status = data.get('doc_status')
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

    text = "📋 Список документов:\n\n"
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

@router.callback_query(F.data == "doc_back")
async def back_to_doc_menu(callback: CallbackQuery):
    await callback.message.delete()
    employee = await get_employee(callback.from_user.id)
    await callback.message.answer("Меню документов", reply_markup=doc_main_menu_keyboard())
    await callback.answer()
