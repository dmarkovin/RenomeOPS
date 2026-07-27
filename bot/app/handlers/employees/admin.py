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
from app.states.employees.role_change import RoleChange

router = Router()

# ===== Главное меню администратора =====
@router.message(F.text == "👥 Сотрудники")
async def employees_menu(message: Message):
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
        status = "✅" if emp.active else "❌"
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

# ===== Смена роли (автоматически меняет команду) =====
@router.callback_query(F.data.startswith("emp_change_role:"))
async def change_role_start(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split(":")[1])
    admin = await get_employee(callback.from_user.id)
    if not admin or admin.role != UserRole.ADMIN:
        await callback.answer("Нет прав", show_alert=True)
        return
    emp = await get_employee_by_id(user_id)
    if not emp:
        await callback.answer("Сотрудник не найден", show_alert=True)
        return
    await state.set_state(RoleChange.select_role)
    await state.update_data(user_id=user_id)
    await callback.message.edit_text(
        f"Выберите новую роль для {emp.full_name}:",
        reply_markup=role_selection_keyboard(user_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("emp_set_role:"), StateFilter(RoleChange.select_role))
async def set_role_with_reason(callback: CallbackQuery, state: FSMContext):
    _, user_id_str, role_str = callback.data.split(":")
    user_id = int(user_id_str)
    new_role = UserRole(role_str)
    await state.update_data(new_role=new_role)
    await state.set_state(RoleChange.reason)
    await callback.message.edit_text("Введите обоснование для смены роли:")
    await callback.answer()

@router.message(StateFilter(RoleChange.reason), F.text)
async def process_role_change_reason(message: Message, state: FSMContext):
    reason = message.text
    data = await state.get_data()
    user_id = data.get("user_id")
    new_role = data.get("new_role")
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка")
        await state.clear()
        return

    # Создаём задачу для администратора
    from app.services.tasks.service import create_task, assign_task_to_user
    from app.services.employees.service import get_all_employees
    from app.services.notification_service import notify_admins

    task = await create_task(
        title=f"Запрос на смену роли для {employee.full_name}",
        description=f"Пользователь {employee.full_name} запросил смену роли на {new_role.value}.\nОбоснование: {reason}",
        created_by=employee.id,
        priority=4,
        is_feedback=True
    )

    admins = await get_all_employees(role=UserRole.ADMIN, active=True)
    if admins:
        admin = admins[0]
        await assign_task_to_user(task.id, admin.id, employee.id)
        await notify_admins(f"📢 Запрос на смену роли от {employee.full_name}:\n{reason}")
        await message.answer(f"✅ Запрос на смену роли отправлен администратору. Задача #{task.id} создана.")
    else:
        await message.answer("⚠️ Нет доступных администраторов. Запрос не назначен.")

    await state.clear()

# ===== Смена команды (вручную) =====
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
    await callback.answer(
        f"✅ Команда изменена на {new_team.value if new_team else '—'}",
        show_alert=True
    )
    await show_employee_card(callback)

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

# ===== Поиск сотрудников =====
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
