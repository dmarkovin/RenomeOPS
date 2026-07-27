from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter

from app.services.employees.service import get_employee
from app.services.reception.key_service import create_key, get_key, get_keys, return_key
from app.database.models import UserRole
from app.keyboards.reception_keys import (
    key_list_keyboard, key_action_keyboard, key_main_menu_keyboard
)
from app.keyboards.main_menu import main_menu_keyboard

router = Router()

class KeyCreate(StatesGroup):
    key_number = State()
    recipient = State()
    purpose = State()
    comment = State()
    confirm = State()

@router.message(F.text == "🔑 Ключи")
async def keys_menu(message: Message, page: int = 1, status: str = None):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE):
        await message.answer("У вас нет прав.")
        return

    limit = 10
    offset = (page - 1) * limit
    keys = await get_keys(status=status, limit=limit, offset=offset)
    total = len(keys)  # упрощённо
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    if not keys:
        await message.answer("Нет записей.", reply_markup=key_main_menu_keyboard())
        return

    text = "📋 Список ключей:\n\n"
    for k in keys:
        status_emoji = "🔑" if k.status == "issued" else "✅"
        text += f"{status_emoji} #{k.id} {k.key_number} – {k.recipient} ({k.status})\n"
    await message.answer(text, reply_markup=key_list_keyboard(keys, page, total_pages))


@router.message(F.text == "📋 Список выданных")
async def list_issued_keys(message: Message):
    await keys_menu(message, status="issued")


@router.message(F.text == "📋 Возвращённые")
async def list_returned_keys(message: Message):
    await keys_menu(message, status="returned")


@router.message(F.text == "➕ Выдать ключ")
async def start_create_key(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE):
        await message.answer("Нет прав.")
        return
    await state.clear()
    await state.set_state(KeyCreate.key_number)
    await message.answer("Введите номер ключа:")


@router.message(KeyCreate.key_number)
async def process_key_number(message: Message, state: FSMContext):
    await state.update_data(key_number=message.text.strip())
    await state.set_state(KeyCreate.recipient)
    await message.answer("Введите ФИО получателя:")


@router.message(KeyCreate.recipient)
async def process_recipient(message: Message, state: FSMContext):
    await state.update_data(recipient=message.text.strip())
    await state.set_state(KeyCreate.purpose)
    await message.answer("Введите основание (или '-' для пропуска):")


@router.message(KeyCreate.purpose)
async def process_purpose(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(purpose=text if text != "-" else "")
    await state.set_state(KeyCreate.comment)
    await message.answer("Введите комментарий (или '-' для пропуска):")


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
    await message.answer(text, reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="✅ Да, выдать")], [types.KeyboardButton(text="❌ Отмена")]],
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


# Карточка
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
    await callback.message.edit_text(text, reply_markup=key_action_keyboard(k.id, k.status))
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


@router.callback_query(F.data.startswith("key_page:"))
async def paginate_keys(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    await keys_menu(callback.message, page)
    await callback.answer()


@router.callback_query(F.data == "key_back")
async def back_to_key_menu(callback: CallbackQuery):
    await callback.message.delete()
    employee = await get_employee(callback.from_user.id)
    await callback.message.answer("Меню ключей", reply_markup=key_main_menu_keyboard())
    await callback.answer()
