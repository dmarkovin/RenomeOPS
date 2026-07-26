from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.services.employees.service import get_employee
from app.services.reception.document_service import (
    create_document, get_document, get_documents,
    return_document, archive_document
)
from app.database.models import UserRole
from app.keyboards.reception_documents import (
    document_list_keyboard, document_action_keyboard, document_main_menu_keyboard
)
from app.keyboards.main_menu import main_menu_keyboard

router = Router()

class DocumentCreate(StatesGroup):
    doc_type = State()
    number = State()
    title = State()
    recipient = State()
    sender = State()
    storage_location = State()
    issued_to = State()
    comment = State()
    confirm = State()

@router.message(F.text == "📄 Документы")
async def documents_menu(message: Message, page: int = 1, doc_type: str = None):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE):
        await message.answer("У вас нет прав.")
        return
    await message.answer("📄 Управление документами:", reply_markup=document_main_menu_keyboard())

# === Создание документа ===
@router.message(F.text.startswith("➕ "))
async def start_create_document(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE):
        await message.answer("Нет прав.")
        return
    text = message.text
    if "Входящий" in text:
        doc_type = "incoming"
    elif "Исходящий" in text:
        doc_type = "outgoing"
    elif "На хранение" in text:
        doc_type = "storage"
    elif "Выдать" in text:
        doc_type = "issued"
    else:
        await message.answer("Неизвестный тип документа.")
        return
    await state.clear()
    await state.update_data(doc_type=doc_type)
    await state.set_state(DocumentCreate.number)
    await message.answer("Введите номер документа:")

@router.message(DocumentCreate.number)
async def process_number(message: Message, state: FSMContext):
    await state.update_data(number=message.text.strip())
    await state.set_state(DocumentCreate.title)
    await message.answer("Введите краткое описание (название):")

@router.message(DocumentCreate.title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    data = await state.get_data()
    doc_type = data.get("doc_type")
    if doc_type == "incoming":
        await state.set_state(DocumentCreate.sender)
        await message.answer("Введите отправителя:")
    elif doc_type == "outgoing":
        await state.set_state(DocumentCreate.recipient)
        await message.answer("Введите получателя:")
    elif doc_type == "storage":
        await state.set_state(DocumentCreate.storage_location)
        await message.answer("Введите место хранения:")
    elif doc_type == "issued":
        await state.set_state(DocumentCreate.issued_to)
        await message.answer("Введите кому выдается:")

@router.message(DocumentCreate.sender)
async def process_sender(message: Message, state: FSMContext):
    await state.update_data(sender=message.text.strip())
    await state.set_state(DocumentCreate.comment)
    await message.answer("Введите комментарий (или '-' для пропуска):")

@router.message(DocumentCreate.recipient)
async def process_recipient(message: Message, state: FSMContext):
    await state.update_data(recipient=message.text.strip())
    await state.set_state(DocumentCreate.comment)
    await message.answer("Введите комментарий (или '-' для пропуска):")

@router.message(DocumentCreate.storage_location)
async def process_storage(message: Message, state: FSMContext):
    await state.update_data(storage_location=message.text.strip())
    await state.set_state(DocumentCreate.comment)
    await message.answer("Введите комментарий (или '-' для пропуска):")

@router.message(DocumentCreate.issued_to)
async def process_issued_to(message: Message, state: FSMContext):
    await state.update_data(issued_to=message.text.strip())
    await state.set_state(DocumentCreate.comment)
    await message.answer("Введите комментарий (или '-' для пропуска):")

@router.message(DocumentCreate.comment)
async def process_comment(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(comment=text if text != "-" else "")
    await state.set_state(DocumentCreate.confirm)
    data = await state.get_data()
    text = (
        f"📄 Проверьте данные документа:\n\n"
        f"Тип: {data.get('doc_type')}\n"
        f"Номер: {data.get('number')}\n"
        f"Название: {data.get('title')}\n"
        f"Отправитель: {data.get('sender') or '—'}\n"
        f"Получатель: {data.get('recipient') or '—'}\n"
        f"Место хранения: {data.get('storage_location') or '—'}\n"
        f"Кому выдан: {data.get('issued_to') or '—'}\n"
        f"Комментарий: {data.get('comment') or '—'}\n\n"
        f"Подтвердить создание?"
    )
    await message.answer(text, reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="✅ Да, создать")], [types.KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))

@router.message(DocumentCreate.confirm, F.text == "✅ Да, создать")
async def confirm_create_document(message: Message, state: FSMContext):
    data = await state.get_data()
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка.")
        await state.clear()
        return
    try:
        doc = await create_document(
            doc_type=data.get("doc_type"),
            number=data.get("number"),
            title=data.get("title"),
            recipient=data.get("recipient"),
            sender=data.get("sender"),
            storage_location=data.get("storage_location"),
            issued_to=data.get("issued_to"),
            comment=data.get("comment"),
            created_by=employee.id
        )
        await state.clear()
        await message.answer(f"✅ Документ #{doc.id} создан.", reply_markup=document_main_menu_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", parse_mode=None)
        await state.clear()

@router.message(DocumentCreate.confirm, F.text == "❌ Отмена")
async def cancel_create_document(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено", reply_markup=document_main_menu_keyboard())

# === Список документов ===
@router.message(F.text == "📋 Список документов")
async def list_documents(message: Message, page: int = 1):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE):
        await message.answer("Нет прав.")
        return
    limit = 10
    offset = (page - 1) * limit
    docs = await get_documents(limit=limit, offset=offset)
    total = len(docs)
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    if not docs:
        await message.answer("Нет документов.", reply_markup=document_main_menu_keyboard())
        return
    text = "📄 Список документов:\n\n"
    for d in docs:
        emoji = "📥" if d.doc_type == "incoming" else "📤" if d.doc_type == "outgoing" else "📦" if d.doc_type == "storage" else "📋"
        text += f"{emoji} #{d.id} {d.title} ({d.doc_type})\n"
    await message.answer(text, reply_markup=document_list_keyboard(docs, page, total_pages))

# === Карточка документа ===
@router.callback_query(F.data.startswith("doc:"))
async def show_document(callback: CallbackQuery):
    doc_id = int(callback.data.split(":")[1])
    doc = await get_document(doc_id)
    if not doc:
        await callback.answer("Не найден", show_alert=True)
        return
    text = (
        f"📄 Документ #{doc.id}\n"
        f"Тип: {doc.doc_type}\n"
        f"Номер: {doc.number}\n"
        f"Название: {doc.title}\n"
        f"Отправитель: {doc.sender or '—'}\n"
        f"Получатель: {doc.recipient or '—'}\n"
        f"Место хранения: {doc.storage_location or '—'}\n"
        f"Кому выдан: {doc.issued_to or '—'}\n"
        f"Дата выдачи: {doc.issued_at.strftime('%d.%m.%Y %H:%M') if doc.issued_at else '—'}\n"
        f"Дата возврата: {doc.returned_at.strftime('%d.%m.%Y %H:%M') if doc.returned_at else '—'}\n"
        f"Статус: {doc.status}\n"
        f"Комментарий: {doc.comment or '—'}"
    )
    await callback.message.edit_text(text, reply_markup=document_action_keyboard(doc.id, doc.doc_type, doc.status))
    await callback.answer()

@router.callback_query(F.data.startswith("doc_return:"))
async def return_document_callback(callback: CallbackQuery):
    doc_id = int(callback.data.split(":")[1])
    doc = await return_document(doc_id)
    if doc:
        await callback.answer("✅ Документ возвращён")
        await show_document(callback)
    else:
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("doc_archive:"))
async def archive_document_callback(callback: CallbackQuery):
    doc_id = int(callback.data.split(":")[1])
    doc = await archive_document(doc_id)
    if doc:
        await callback.answer("📦 В архиве")
        await show_document(callback)
    else:
        await callback.answer("Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("doc_page:"))
async def paginate_documents(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    await list_documents(callback.message, page)
    await callback.answer()

@router.callback_query(F.data == "doc_back")
async def back_to_document_menu(callback: CallbackQuery):
    await callback.message.delete()
    employee = await get_employee(callback.from_user.id)
    await callback.message.answer("Меню документов", reply_markup=document_main_menu_keyboard())
    await callback.answer()
