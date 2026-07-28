from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter

from app.services.employees.service import get_employee
from app.services.reception.delivery_service import create_delivery, get_all_deliveries, get_delivery, update_delivery_status
from app.services.reception.document_service import create_document, get_documents, get_document, update_document_status
from app.database.models import UserRole
from app.keyboards.reception import reception_menu_keyboard, delivery_menu_keyboard, document_menu_keyboard

router = Router()

class DeliveryCreate(StatesGroup):
    recipient = State()
    apartment = State()
    courier = State()
    comment = State()
    photo = State()
    confirm = State()

class DocumentCreate(StatesGroup):
    name = State()
    type = State()
    sender = State()
    recipient = State()
    comment = State()
    photo = State()
    confirm = State()

@router.message(F.text == "📦 Доставка")
async def reception_menu(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE):
        await message.answer("У вас нет прав.")
        return
    await message.answer("Выберите тип:", reply_markup=reception_menu_keyboard())

# ---- Посылка ----
@router.message(F.text == "📦 Посылка")
async def delivery_menu(message: Message):
    await message.answer("📦 Меню посылок:", reply_markup=delivery_menu_keyboard())

@router.message(F.text == "➕ Новая посылка")
async def start_delivery(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка")
        return
    await state.clear()
    await state.set_state(DeliveryCreate.recipient)
    await message.answer("Введите ФИО получателя:", reply_markup=ReplyKeyboardRemove())

@router.message(StateFilter(DeliveryCreate.recipient), F.text)
async def delivery_recipient(message: Message, state: FSMContext):
    await state.update_data(recipient=message.text.strip())
    await state.set_state(DeliveryCreate.apartment)
    await message.answer("Введите номер квартиры (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(StateFilter(DeliveryCreate.apartment), F.text)
async def delivery_apartment(message: Message, state: FSMContext):
    text = message.text.strip()
    apartment = int(text) if text.isdigit() else None
    await state.update_data(apartment=apartment)
    await state.set_state(DeliveryCreate.courier)
    await message.answer("Введите название курьерской службы (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(StateFilter(DeliveryCreate.courier), F.text)
async def delivery_courier(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(courier=text if text != "-" else "")
    await state.set_state(DeliveryCreate.comment)
    await message.answer("Введите комментарий (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(StateFilter(DeliveryCreate.comment), F.text)
async def delivery_comment(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(comment=text if text != "-" else "")
    await state.set_state(DeliveryCreate.photo)
    await message.answer("🖼 Пришлите фото (опционально) или нажмите **Готово**:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Готово")]],
        resize_keyboard=True
    ))

@router.message(StateFilter(DeliveryCreate.photo), F.photo)
async def delivery_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Добавлено фото ({len(photos)})")

@router.message(StateFilter(DeliveryCreate.photo), F.text == "✅ Готово")
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

@router.message(StateFilter(DeliveryCreate.confirm), F.text == "✅ Да, создать")
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
        await message.answer(f"✅ Посылка #{delivery.id} создана!", reply_markup=delivery_menu_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", parse_mode=None)
        await state.clear()

@router.message(StateFilter(DeliveryCreate.confirm), F.text == "❌ Отмена")
async def delivery_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено", reply_markup=delivery_menu_keyboard())

# ---- Документ ----
@router.message(F.text == "📄 Документ")
async def document_menu(message: Message):
    await message.answer("📄 Меню документов:", reply_markup=document_menu_keyboard())

@router.message(F.text == "➕ Новый документ")
async def start_document(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка")
        return
    await state.clear()
    await state.set_state(DocumentCreate.name)
    await message.answer("Введите название документа:", reply_markup=ReplyKeyboardRemove())

@router.message(StateFilter(DocumentCreate.name), F.text)
async def document_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(DocumentCreate.type)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Входящий")],
            [KeyboardButton(text="📤 Исходящий")],
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите тип документа:", reply_markup=kb)

@router.message(StateFilter(DocumentCreate.type), F.text.in_(["📥 Входящий", "📤 Исходящий"]))
async def document_type(message: Message, state: FSMContext):
    doc_type = "incoming" if message.text == "📥 Входящий" else "outgoing"
    await state.update_data(type=doc_type)
    await state.set_state(DocumentCreate.sender)
    await message.answer("Введите отправителя (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(StateFilter(DocumentCreate.sender), F.text)
async def document_sender(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(sender=text if text != "-" else "")
    await state.set_state(DocumentCreate.recipient)
    await message.answer("Введите получателя (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(StateFilter(DocumentCreate.recipient), F.text)
async def document_recipient(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(recipient=text if text != "-" else "")
    await state.set_state(DocumentCreate.comment)
    await message.answer("Введите комментарий (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(StateFilter(DocumentCreate.comment), F.text)
async def document_comment(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(comment=text if text != "-" else "")
    await state.set_state(DocumentCreate.photo)
    await message.answer("🖼 Пришлите фото (опционально) или нажмите **Готово**:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Готово")]],
        resize_keyboard=True
    ))

@router.message(StateFilter(DocumentCreate.photo), F.photo)
async def document_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Добавлено фото ({len(photos)})")

@router.message(StateFilter(DocumentCreate.photo), F.text == "✅ Готово")
async def document_ready(message: Message, state: FSMContext):
    await state.set_state(DocumentCreate.confirm)
    data = await state.get_data()
    text = (
        f"📄 Проверьте данные:\n\n"
        f"Название: {data['name']}\n"
        f"Тип: {data.get('type')}\n"
        f"Отправитель: {data.get('sender') or '—'}\n"
        f"Получатель: {data.get('recipient') or '—'}\n"
        f"Комментарий: {data.get('comment') or '—'}\n"
        f"Фото: {len(data.get('photos', []))} шт.\n\n"
        f"Подтвердить создание?"
    )
    await message.answer(text, reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Да, создать")], [KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))

@router.message(StateFilter(DocumentCreate.confirm), F.text == "✅ Да, создать")
async def document_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка.")
        await state.clear()
        return
    try:
        doc = await create_document(
            name=data['name'],
            doc_type=data.get('type'),
            sender=data.get('sender'),
            recipient=data.get('recipient'),
            comment=data.get('comment'),
            photo_ids=data.get('photos', []),
            created_by=employee.id
        )
        await state.clear()
        await message.answer(f"✅ Документ #{doc.id} создан!", reply_markup=document_menu_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", parse_mode=None)
        await state.clear()

@router.message(StateFilter(DocumentCreate.confirm), F.text == "❌ Отмена")
async def document_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено", reply_markup=document_menu_keyboard())

# ---- Список активных и архив (заглушки) ----
@router.message(F.text == "📋 Активные посылки")
async def list_active_deliveries(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка")
        return
    deliveries = await get_all_deliveries(status=None, limit=20)
    if not deliveries:
        await message.answer("Нет активных посылок.")
        return
    text = "📋 Активные посылки:\n\n"
    for d in deliveries:
        status_emoji = "🟡" if d.status == "pending" else "🔵" if d.status == "received" else "✅"
        text += f"{status_emoji} #{d.id} {d.recipient} (кв.{d.apartment or '—'}) – {d.status}\n"
    await message.answer(text, reply_markup=delivery_menu_keyboard())

@router.message(F.text == "📦 Архив посылок")
async def archive_deliveries(message: Message):
    # можно фильтровать по статусу completed
    await message.answer("📦 Архив посылок (в разработке)", reply_markup=delivery_menu_keyboard())

@router.message(F.text == "📋 Активные документы")
async def list_active_documents(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка")
        return
    docs = await get_documents(status='active', limit=20)
    if not docs:
        await message.answer("Нет активных документов.")
        return
    text = "📋 Активные документы:\n\n"
    for d in docs:
        type_emoji = "📥" if d.doc_type == "incoming" else "📤"
        text += f"{type_emoji} #{d.id} {d.name} ({d.doc_type}) – {d.status}\n"
    await message.answer(text, reply_markup=document_menu_keyboard())

@router.message(F.text == "📦 Архив документов")
async def archive_documents(message: Message):
    await message.answer("📦 Архив документов (в разработке)", reply_markup=document_menu_keyboard())

@router.message(F.text == "⬅️ Назад")
async def back_from_reception(message: Message):
    employee = await get_employee(message.from_user.id)
    if employee and employee.role == UserRole.CONCIERGE:
        from app.keyboards.concierge import concierge_keyboard
        await message.answer("Главное меню", reply_markup=concierge_keyboard())
    else:
        from app.keyboards.main_menu import main_menu_keyboard
        await message.answer("Главное меню", reply_markup=main_menu_keyboard(employee.role) if employee else None)
