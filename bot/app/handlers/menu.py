from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.services.employees.service import get_employee, count_employees
from app.services.tasks.service import (
    count_open_tasks,
    count_checking_tasks,
    count_tasks_by_status,
    get_open_tasks,
)
from app.services.services.service import get_all_orders
from app.keyboards.main_menu import main_menu_keyboard
from app.database.models import UserRole
from app.keyboards.tasks import get_priority_name
import logging

logger = logging.getLogger(__name__)
router = Router()

async def show_main_menu(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка. Попробуйте /start")
        return
    if not employee.active:
        await message.answer("Ваш аккаунт заблокирован. Обратитесь к администратору.")
        return
    await message.answer(
        "🏠 Главное меню:",
        reply_markup=main_menu_keyboard(employee.role)
    )

@router.message(F.text == "🏠 Главное меню")
async def main_menu_handler(message: Message, state: FSMContext):
    await state.clear()
    employee = await get_employee(message.from_user.id)
    if employee:
        await message.answer("🏠 Главное меню:", reply_markup=main_menu_keyboard(employee.role))
    else:
        await message.answer("🏠 Главное меню")

@router.message(F.text == "📊 Статистика")
async def show_statistics(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR):
        await message.answer("Только для администратора и директора.")
        return
    total_open = await count_open_tasks()
    total_checking = await count_checking_tasks()
    total_closed = await count_tasks_by_status("closed")
    total_waiting = await count_tasks_by_status("waiting")
    total_paused = await count_tasks_by_status("paused")
    total_employees = await count_employees(active=True)
    orders = await get_all_orders(limit=1000)
    total_orders = len([o for o in orders if o.status == "pending"])

    tasks = await get_open_tasks(limit=1000, offset=0)
    priority_stats = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for task in tasks:
        priority = int(task.priority) if task.priority is not None else 3
        if priority in priority_stats:
            priority_stats[priority] += 1

    text = (
        f"📊 **Статистика системы**\n\n"
        f"👥 Активных сотрудников: {total_employees}\n"
        f"📋 Открытых заявок: {total_open}\n"
        f"⏳ Ожидают: {total_waiting}\n"
        f"⏸ Приостановлено: {total_paused}\n"
        f"🔄 На проверке: {total_checking}\n"
        f"✅ Закрыто: {total_closed}\n"
        f"💳 Активных заказов услуг: {total_orders}\n\n"
        f"**Приоритеты открытых заявок:**\n"
        f"🚨 Аварийный: {priority_stats.get(5, 0)}\n"
        f"⚠️ Критичный: {priority_stats.get(4, 0)}\n"
        f"🔶 Высокий: {priority_stats.get(3, 0)}\n"
        f"🔼 Средний: {priority_stats.get(2, 0)}\n"
        f"ℹ️ Низкий: {priority_stats.get(1, 0)}"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "⚙️ Настройки")
async def settings_handler(message: Message):
    await message.answer("⚙️ Настройки будут доступны в следующих версиях.")

@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    employee = await get_employee(callback.from_user.id)
    if employee:
        await callback.message.answer("🏠 Главное меню:", reply_markup=main_menu_keyboard(employee.role))
    else:
        await callback.message.answer("🏠 Главное меню")
    await callback.answer()
