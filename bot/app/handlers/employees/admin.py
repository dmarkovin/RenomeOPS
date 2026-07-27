from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter

from app.services.employees.service import (
    get_all_employees,
    count_employees,
    get_employee_by_id,
    block_employee,
    activate_employee_by_admin,
    delete_employee,
    get_employee,
    update_employee_role,
    update_employee_team,
    get_default_team_for_role,
)
from app.keyboards.employees.admin import employees_admin_menu
from app.keyboards.employees.list import employee_list_keyboard, employee_card_keyboard
from app.keyboards.employees.roles import role_selection_keyboard
from app.keyboards.employees.teams import team_selection_keyboard
from app.database.models import UserRole, Team
from app.keyboards.admin import admin_keyboard
from app.states.employees.search import EmployeeSearch

router = Router()

@router.message(F.text == "👥 Сотрудники")
async def employees_menu(message: Message):
    admin = await get_employee(message.from_user.id)
    if not admin or admin.role != UserRole.ADMIN:
        await message.answer("У вас нет прав.")
        return
    await message.answer("👥 Управление сотрудниками:", reply_markup=employees_admin_menu())

@router.message(F.text == "📋 Список сотрудников")
async def list_employees(message: Message, page: int = 1):
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
        status = "✅" if emp.active else "❌"
        text += f"ID: {emp.id} | {emp.full_name} | {emp.role.value} | {status}\n"

    await message.answer(text, reply_markup=employee_list_keyboard(employees, page, total_pages))

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
        status = "✅" if emp.active else "❌"
        text += f"ID: {emp.id} | {emp.full_name} | {emp.role.value} | {status}\n"

    await callback.message.edit_text(text, reply_markup=employee_list_keyboard(employees, page, total_pages))
    await callback.answer()

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
    await callback.message.edit_text(text, reply_markup=employee_card_keyboard(emp.id, emp.active))
    await callback.answer()

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

@router.callback_query(F.data.startswith("emp_change_role:"))
async def change_role_start(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    admin = await get_employee(callback.from_user.id)
    if not admin or admin.role != UserRole.ADMIN:
        await callback.answer("Нет прав", show_alert=True)
        return
    emp = await get_employee_by_id(user_id)
    if not emp:
        await callback.answer("Сотрудник не найден", show_alert=True)
        return
    await callback.message.edit_text(
        f"Выберите новую роль для {emp.full_name}:",
        reply_markup=role_selection_keyboard(user_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("emp_set_role:"))
async def set_role(callback: CallbackQuery):
    _, user_id_str, role_str = callback.data.split(":")
    user_id = int(user_id_str)
    new_role = UserRole(role_str)

    admin = await get_employee(callback.from_user.id)
    if not admin or admin.role != UserRole.ADMIN:
        await callback.answer("Нет прав", show_alert=True)
        return

    # Меняем роль
    emp = await update_employee_role(user_id, new_role)
    if not emp:
        await callback.answer("Ошибка изменения роли", show_alert=True)
        return

    # Автоматически устанавливаем команду по умолчанию для новой роли
    default_team = get_default_team_for_role(new_role)
    if default_team is not None:
        await update_employee_team(user_id, default_team)
    else:
        # Если для роли нет команды (ADMIN, DIRECTOR), очищаем команду
        await update_employee_team(user_id, None)

    await callback.answer(f"✅ Роль изменена на {new_role.value}, команда автоматически обновлена.", show_alert=True)
    await show_employee_card(callback)

@router.callback_query(F.data.startswith("emp_change_team:"))
async def change_team_start(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    admin = await get_employee(callback.from_user.id)
    if not admin or admin.role != UserRole.ADMIN:
        await callback.answer("Нет прав", show_alert=True)
        return
    emp = await get_employee_by_id(user_id)
    if not emp:
        await callback.answer("Сотрудник не найден", show_alert=True)
        return
    await callback.message.edit_text(
        f"Выберите новую команду для {emp.full_name}:",
        reply_markup=team_selection_keyboard(user_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("emp_set_team:"))
async def set_team(callback: CallbackQuery):
    _, user_id_str, team_str = callback.data.split(":")
    user_id = int(user_id_str)
    new_team = Team(team_str) if team_str != "None" else None
    admin = await get_employee(callback.from_user.id)
    if not admin or admin.role != UserRole.ADMIN:
        await callback.answer("Нет прав", show_alert=True)
        return
    emp = await update_employee_team(user_id, new_team)
    if not emp:
        await callback.answer("Ошибка", show_alert=True)
        return
    await callback.answer(f"✅ Команда изменена на {new_team.value if new_team else '—'}", show_alert=True)
    await show_employee_card(callback)

@router.callback_query(F.data == "emp_back")
async def back_to_employees_menu(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("👥 Управление сотрудниками:", reply_markup=employees_admin_menu())
    await callback.answer()
    await callback.message.delete()
    await list_employees(callback.message, page=1)
    await callback.answer()

@router.message(F.text == "⬅️ Назад")
async def back_to_admin_menu(message: Message):
    admin = await get_employee(message.from_user.id)
    if admin and admin.role == UserRole.ADMIN:
        await message.answer("👑 Главное меню администратора", reply_markup=admin_keyboard())
    else:
        await message.answer("Возврат...")

@router.message(F.text == "🔍 Поиск")
async def start_search(message: Message, state: FSMContext):
    admin = await get_employee(message.from_user.id)
    if not admin or admin.role != UserRole.ADMIN:
        await message.answer("Нет прав.")
        return
    await state.set_state(EmployeeSearch.query)
    await message.answer("Введите ФИО или телефон для поиска:")

@router.message(StateFilter(EmployeeSearch.query), F.text)
async def process_search(message: Message, state: FSMContext):
    query = message.text.strip()
    if len(query) < 2:
        await message.answer("Введите минимум 2 символа.")
        return
    employees = await get_all_employees(search=query)
    if not employees:
        await message.answer("Ничего не найдено.")
        await state.clear()
        return
    text = "🔍 Результаты поиска:\n\n"
    for emp in employees:
        status = "✅" if emp.active else "❌"
        text += f"{status} {emp.full_name} (ID: {emp.id}) | {emp.role.value}\n"
    await message.answer(text)
    await state.clear()

@router.callback_query(F.data == "emp_search")
async def search_from_list(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await start_search(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "emp_back")
async def back_to_employees_menu(callback: CallbackQuery):
    from app.keyboards.employees.admin import employees_admin_menu
    await callback.message.delete()
    await callback.message.answer("👥 Управление сотрудниками:", reply_markup=employees_admin_menu())
    await callback.answer()
