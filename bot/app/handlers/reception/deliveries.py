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

@router.message(F.text == "📦 Доставка")
async def reception_menu(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE):
        await message.answer("У вас нет прав.")
        return
    await message.answer("📦 Меню доставки:", reply_markup=reception_menu_keyboard())

# ========== Создание посылки ==========
@router.message(F.text == "📦 Новая посылка")
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
        await message.answer("Выберите действие:", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", parse_mode=None)
        await state.clear()

@router.message(DeliveryCreate.confirm, F.text == "❌ Отмена")
async def delivery_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено", reply_markup=reception_menu_keyboard())

# ... остальная часть файла без изменений (списки, архив, комментарии и т.д.) - но для краткости я пропущу, так как они уже были корректными.
