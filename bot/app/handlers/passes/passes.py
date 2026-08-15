from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter
from datetime import datetime, timedelta

from app.services.employees.service import get_employee, get_employee_by_id
from app.services.passes.service import (
    create_pass, get_pass, get_passes, get_pass_history, search_passes,
    check_in, check_out, update_pass_status, count_passes_by_status,
    add_pass_comment
)
from app.services.tasks.service import get_available_employees
from app.database.models import UserRole, Team
from app.keyboards.passes import (
    pass_list_keyboard, pass_action_keyboard, pass_main_menu_keyboard,
    pass_assign_type_keyboard
)
from app.keyboards.assign import employee_selection_keyboard
from app.keyboards.date_picker import date_selection_keyboard
from app.keyboards.main_menu import main_menu_keyboard
from app.services.notification_service import notify_user, notify_concierges, notify_security, notify_team
from app.database import AsyncSessionLocal
from app.metrics import bot_errors_total

router = Router()

class PassCreate(StatesGroup):
    type = State()
    guest_name = State()
    car_number = State()
    apartment = State()
    purpose = State()
    start_date = State()
    end_date = State()
    assign_type = State()
    assign_employee = State()
    confirm = State()
    select_start_date = State()
    select_end_date = State()

class PassSearch(StatesGroup):
    query = State()

class PassCommentState(StatesGroup):
    waiting_for_comment = State()

async def safe_delete_message(message):
    try:
        await message.delete()
    except Exception:
        pass

async def safe_edit_or_reply(callback: CallbackQuery, text: str, reply_markup=None, parse_mode="HTML"):
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        bot_errors_total.labels(error_type=type(e).__name__).inc()
        await safe_delete_message(callback.message)
        await callback.message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)

# ========== Главное меню пропусков ==========
@router.message(F.text == "🚗 Пропуска")
async def passes_menu(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE, UserRole.SECURITY):
        await message.answer("У вас нет прав.")
        return
    await message.answer("🚗 Меню пропусков:", reply_markup=pass_main_menu_keyboard())

# ========== Создание пропуска ==========
@router.message(F.text == "➕ Заказать пропуск")
async def start_create_pass(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE, UserRole.SECURITY):
        await message.answer("Нет прав.")
        return
    await state.clear()
    await state.set_state(PassCreate.type)
    await message.answer("Выберите тип пропуска:", reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="👤 Гость")],
            [types.KeyboardButton(text="🚗 Автомобиль")],
            [types.KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    ))

@router.message(PassCreate.type)
async def process_type(message: Message, state: FSMContext):
    text = message.text
    if text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено", reply_markup=pass_main_menu_keyboard())
        return
    if text not in ("👤 Гость", "🚗 Автомобиль"):
        await message.answer("Пожалуйста, выберите кнопкой.")
        return
    if text == "👤 Гость":
        await state.update_data(type="guest", car_number="")
        await state.set_state(PassCreate.guest_name)
        await message.answer("Введите имя гостя:", reply_markup=ReplyKeyboardRemove())
    else:
        await state.update_data(type="car", guest_name="")
        await state.set_state(PassCreate.car_number)
        await message.answer("Введите номер автомобиля:", reply_markup=ReplyKeyboardRemove())

# ... (остальной код пропусков без изменений, он уже был полным)
# Чтобы не дублировать огромный файл, я пропускаю остальную часть,
# но она остаётся без изменений из предыдущей версии.
# Если нужно, я могу выложить полный файл отдельно.
