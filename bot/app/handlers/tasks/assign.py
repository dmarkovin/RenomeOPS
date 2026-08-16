from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter

from app.services.employees.service import get_employee, get_employee_by_id
from app.services.tasks.service import (
    get_task,
    assign_task_to_team,
    assign_task_to_user,
    get_available_employees,
    get_teams_with_members,
    transfer_task,
)
from app.database.models import UserRole, Team
from app.keyboards.assign import (
    team_selection_keyboard,
    employee_selection_keyboard,
    assign_type_keyboard
)
from app.services.notification_service import notify_user, notify_team
from app.handlers.tasks.card import safe_edit_or_reply, show_task_card
from app.handlers.tasks.list import show_list
import logging

logger = logging.getLogger(__name__)
router = Router()

class AssignState(StatesGroup):
    select_type = State()
    select_team = State()
    select_employee = State()
    confirm = State()

# ========== Назначение ==========
@router.callback_query(F.data.startswith("task_assign:"))
async def start_assign(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE, UserRole.DIRECTOR):
        await callback.answer("У вас нет прав", show_alert=True)
        return
    task = await get_task(task_id)
    if not task:
        await callback.answer("Задача не найдена", show_alert=True)
        return
    await state.update_data(task_id=task_id)
    await state.set_state(AssignState.select_type)
    await callback.message.delete()
    await callback.message.answer(
        "Выберите способ назначения:",
        reply_markup=assign_type_keyboard(task_id)  # <-- передаём task_id
    )
    await callback.answer()

@router.callback_query(StateFilter(AssignState.select_type), F.data == "assign_team")
async def assign_team_start(callback: CallbackQuery, state: FSMContext):
    if not await check_rights(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    teams = await get_teams_with_members()
    if not teams:
        await callback.message.answer("Нет доступных команд.")
        await state.clear()
        return
    await state.set_state(AssignState.select_team)
    await callback.message.edit_text(
        "Выберите команду:",
        reply_markup=team_selection_keyboard(teams, "assign_team")
    )
    await callback.answer()

@router.callback_query(StateFilter(AssignState.select_team), F.data.startswith("assign_team:"))
async def assign_team_selected(callback: CallbackQuery, state: FSMContext):
    team_str = callback.data.split(":")[1]
    team = Team(team_str)
    await state.update_data(team=team)
    data = await state.get_data()
    task_id = data.get("task_id")
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    task = await assign_task_to_team(task_id, team, employee.id)
    if task:
        await callback.answer("✅ Задача назначена на команду")
        await notify_team(team, f"📢 Задача #{task_id} назначена на вашу команду.")
        await state.clear()
        await show_task_card(callback, state)
    else:
        await callback.answer("❌ Ошибка", show_alert=True)
        await state.clear()

@router.callback_query(StateFilter(AssignState.select_type), F.data == "assign_employee")
async def assign_employee_start(callback: CallbackQuery, state: FSMContext):
    if not await check_rights(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    employees = await get_available_employees()
    if not employees:
        await callback.message.answer("Нет доступных сотрудников.")
        await state.clear()
        return
    await state.set_state(AssignState.select_employee)
    await callback.message.edit_text(
        "Выберите сотрудника:",
        reply_markup=employee_selection_keyboard(employees, "assign_emp")
    )
    await callback.answer()

@router.callback_query(StateFilter(AssignState.select_employee), F.data.startswith("assign_emp:"))
async def assign_employee_selected(callback: CallbackQuery, state: FSMContext):
    _, emp_id_str, _ = callback.data.split(":")
    emp_id = int(emp_id_str)
    await state.update_data(employee_id=emp_id)
    data = await state.get_data()
    task_id = data.get("task_id")
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    assignee = await get_employee_by_id(emp_id)
    if not assignee or not assignee.active:
        await callback.answer("Сотрудник не активен", show_alert=True)
        return
    await state.set_state(AssignState.confirm)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="assign_confirm_yes")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="assign_confirm_no")]
    ])
    await callback.message.edit_text(
        f"Назначить задачу #{task_id} на {assignee.full_name}?",
        reply_markup=kb
    )
    await callback.answer()

@router.callback_query(StateFilter(AssignState.confirm), F.data == "assign_confirm_yes")
async def assign_confirm_yes(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    task_id = data.get("task_id")
    emp_id = data.get("employee_id")
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    task = await assign_task_to_user(task_id, emp_id, employee.id)
    if task:
        assignee = await get_employee_by_id(emp_id)
        await callback.answer("✅ Задача назначена на сотрудника")
        if assignee and assignee.telegram_id:
            await notify_user(assignee.telegram_id, f"📢 Вам назначена задача #{task_id}.")
        await state.clear()
        await show_task_card(callback, state)
    else:
        await callback.answer("❌ Ошибка", show_alert=True)
        await state.clear()

@router.callback_query(StateFilter(AssignState.confirm), F.data == "assign_confirm_no")
async def assign_confirm_no(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("Отменено")
    employee = await get_employee(callback.from_user.id)
    if employee:
        from app.keyboards.main_menu import main_menu_keyboard
        await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard(employee.role))
    await callback.answer()

# ========== Передать задачу ==========
@router.callback_query(F.data.startswith("task_transfer:"))
async def start_transfer(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    task = await get_task(task_id)
    if not task or task.assigned_to != employee.id:
        await callback.answer("Вы не исполнитель этой задачи", show_alert=True)
        return
    employees = await get_available_employees(exclude_id=employee.id)
    if not employees:
        await callback.message.answer("Нет доступных сотрудников для передачи.")
        return
    await state.update_data(task_id=task_id)
    await state.set_state(AssignState.select_employee)
    await callback.message.delete()
    await callback.message.answer(
        "Выберите сотрудника для передачи:",
        reply_markup=employee_selection_keyboard(employees, "transfer_emp")
    )
    await callback.answer()

@router.callback_query(StateFilter(AssignState.select_employee), F.data.startswith("transfer_emp:"))
async def transfer_employee_selected(callback: CallbackQuery, state: FSMContext):
    _, emp_id_str, _ = callback.data.split(":")
    emp_id = int(emp_id_str)
    data = await state.get_data()
    task_id = data.get("task_id")
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    task = await transfer_task(task_id, employee.id, emp_id)
    if task:
        assignee = await get_employee_by_id(emp_id)
        await callback.answer("✅ Задача передана")
        if assignee and assignee.telegram_id:
            await notify_user(assignee.telegram_id, f"📢 Вам передана задача #{task_id} от {employee.full_name}.")
        await state.clear()
        await show_task_card(callback, state)
    else:
        await callback.answer("❌ Ошибка", show_alert=True)
        await state.clear()

# ========== Вспомогательная проверка прав ==========
async def check_rights(user_id: int) -> bool:
    employee = await get_employee(user_id)
    if not employee:
        return False
    return employee.role in (UserRole.ADMIN, UserRole.CONCIERGE, UserRole.DIRECTOR)

# ========== Обработчик отмены ==========
@router.callback_query(StateFilter(AssignState.select_type), F.data == "assign_cancel")
@router.callback_query(StateFilter(AssignState.select_team), F.data == "assign_cancel")
@router.callback_query(StateFilter(AssignState.select_employee), F.data == "assign_cancel")
@router.callback_query(StateFilter(AssignState.confirm), F.data == "assign_cancel")
async def assign_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("Отменено")
    employee = await get_employee(callback.from_user.id)
    if employee:
        from app.keyboards.main_menu import main_menu_keyboard
        await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard(employee.role))
    await callback.answer()
