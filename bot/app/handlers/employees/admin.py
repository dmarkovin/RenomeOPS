from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.services.employees.service import (
    get_all_employees,
    count_employees,
    get_employee_by_id,
    block_employee,
    activate_employee_by_admin,
    delete_employee,
    get_employee,
)
from app.keyboards.employees.admin import employees_admin_menu
from app.keyboards.employees.list import employee_list_keyboard, employee_card_keyboard
from app.database.models import UserRole
from app.keyboards.admin import admin_keyboard

router = Router()

# ===== Главное меню администратора =====
@router.message(F.text == "👥 Сотрудники")
async def employees_menu(message: Message):
    """Главное меню управления сотрудниками"""
    admin = await get_employee(message.from_user.id)
    if not admin or admin.role != UserRole.ADMIN:
        await message.answer("У вас нет прав.")
        return
    await message.answer(
        "👥 Управление сотрудниками:",
        reply_markup=employees_admin_menu()
    )

# ===== Список сотрудников =====
@router.message(F.text == "📋 Список сотрудников")
async def list_employees(message: Message, page: int = 1):
    """Показать список сотрудников с пагинацией"""
    admin = await get_employee(message.from_user.id)
    if not admin or admin.role != UserRole.ADMIN:
        await message.answer("У вас нет прав.")
        return

    limit = 10
    offset = (page - 1) * limit
    employees = await get_all_employees(limit=limit, offset=offset)
    total = await count_employees()
    total_pages = (total + limit - 1) // limit

    if not employees:
        await message.answer("Нет сотрудников.")
        return

    text = f"📋 Список сотрудников (стр. {page}/{total_pages}):\n\n"
    for emp in employees:
        status = "✅ Активен" if emp.active else "❌ Неактивен"
        text += f"ID: {emp.id} | {emp.full_name} | {emp.role.value} | {status}\n"

    await message.answer(
        text,
        reply_markup=employee_list_keyboard(employees, page, total_pages)
    )

# ===== Пагинация в списке =====
@router.callback_query(F.data.startswith("emp_page:"))
async def paginate_employees(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    admin = await get_employee(callback.from_user.id)
    if not admin or admin.role != UserRole.ADMIN:
        await callback.answer("Нет прав", show_alert=True)
        return

    limit = 10
    offset = (page - 1) * limit
    employees = await get_all_employees(limit=limit, offset=offset)
    total = await count_employees()
    total_pages = (total + limit - 1) // limit

    text = f"📋 Список сотрудников (стр. {page}/{total_pages}):\n\n"
    for emp in employees:
        status = "✅ Активен" if emp.active else "❌ Неактивен"
        text += f"ID: {emp.id} | {emp.full_name} | {emp.role.value} | {status}\n"

    await callback.message.edit_text(
        text,
        reply_markup=employee_list_keyboard(employees, page, total_pages)
    )
    await callback.answer()

# ===== Карточка сотрудника =====
@router.callback_query(F.data.startswith("emp_card:"))
async def show_employee_card(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    emp = await get_employee_by_id(user_id)
    if not emp:
        await callback.answer("Сотрудник не найден", show_alert=True)
        return

    text = (
        f"👤 Карточка сотрудника:\n\n"
        f"ID: {emp.id}\n"
        f"ФИО: {emp.full_name}\n"
        f"Телефон: {emp.phone}\n"
        f"Роль: {emp.role.value}\n"
        f"Команда: {emp.team.value if emp.team else '—'}\n"
        f"Активен: {'✅ Да' if emp.active else '❌ Нет'}\n"
        f"Telegram ID: {emp.telegram_id or 'не привязан'}\n"
        f"Приглашение: {emp.invite_code}\n"
        f"Зарегистрирован: {emp.registered_at.strftime('%d.%m.%Y %H:%M') if emp.registered_at else '—'}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=employee_card_keyboard(emp.id, emp.active)
    )
    await callback.answer()

# ===== Блокировка сотрудника =====
@router.callback_query(F.data.startswith("emp_block:"))
async def block_employee_callback(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    admin = await get_employee(callback.from_user.id)
    if not admin or admin.role != UserRole.ADMIN:
        await callback.answer("Нет прав", show_alert=True)
        return

    emp = await block_employee(user_id)
    if emp:
        await callback.answer("Сотрудник заблокирован", show_alert=True)
        await show_employee_card(callback)
    else:
        await callback.answer("Ошибка", show_alert=True)

# ===== Активация сотрудника =====
@router.callback_query(F.data.startswith("emp_activate:"))
async def activate_employee_callback(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    admin = await get_employee(callback.from_user.id)
    if not admin or admin.role != UserRole.ADMIN:
        await callback.answer("Нет прав", show_alert=True)
        return

    emp = await activate_employee_by_admin(user_id)
    if emp:
        await callback.answer("Сотрудник активирован", show_alert=True)
        await show_employee_card(callback)
    else:
        await callback.answer("Ошибка", show_alert=True)

# ===== Удаление сотрудника =====
@router.callback_query(F.data.startswith("emp_delete:"))
async def delete_employee_callback(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    admin = await get_employee(callback.from_user.id)
    if not admin or admin.role != UserRole.ADMIN:
        await callback.answer("Нет прав", show_alert=True)
        return

    success = await delete_employee(user_id)
    if success:
        await callback.answer("Сотрудник удалён", show_alert=True)
        await callback.message.edit_text("Сотрудник удалён.")
    else:
        await callback.answer("Ошибка", show_alert=True)

# ===== Возврат к списку =====
@router.callback_query(F.data == "emp_back")
async def back_to_employees_list(callback: CallbackQuery):
    await callback.message.delete()
    await list_employees(callback.message, page=1)
    await callback.answer()

# ===== Назад в главное меню админа =====
@router.message(F.text == "⬅️ Назад")
async def back_to_admin_menu(message: Message):
    admin = await get_employee(message.from_user.id)
    if admin and admin.role == UserRole.ADMIN:
        await message.answer("👑 Главное меню администратора", reply_markup=admin_keyboard())
    else:
        await message.answer("Возврат...")

# ===== Заглушки для нереализованных функций =====
@router.message(F.text == "🔍 Поиск")
async def search_employees(message: Message):
    await message.answer("🔍 Функция поиска в разработке.")

@router.message(F.text == "♻️ Активировать")
async def activate_employee(message: Message):
    await message.answer("♻️ Функция активации через список сотрудников. Откройте карточку сотрудника и нажмите 'Активировать'.")

@router.message(F.text == "🚫 Заблокировать")
async def block_employee(message: Message):
    await message.answer("🚫 Функция блокировки через список сотрудников. Откройте карточку сотрудника и нажмите 'Заблокировать'.")
