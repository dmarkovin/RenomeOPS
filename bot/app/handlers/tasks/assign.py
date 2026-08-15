from aiogram.types import ReplyKeyboardRemove
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from app.services.tasks.service import (
    get_task,
    assign_task_to_user,
    assign_task_to_team,
    transfer_task,
    get_available_employees,
    get_teams_with_members,
)
from app.services.employees.service import get_employee, get_employee_by_id
from app.database.models import UserRole, Team
from app.keyboards.assign import (
    employee_selection_keyboard,
    team_selection_keyboard,
    assign_type_keyboard,
)
from app.states.tasks.transfer import TaskTransfer
from app.services.notification_service import notify_user, notify_team
from app.keyboards.task_actions import task_actions_keyboard
from app.handlers.tasks.card import safe_edit_or_reply

router = Router()

# ---------- Назначение ----------
@router.callback_query(F.data.startswith("task_assign:"))
async def assign_task_start(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE, UserRole.DIRECTOR):
        await callback.answer("У вас нет прав на назначение.", show_alert=True)
        return
    task = await get_task(task_id)
    if not task:
        await callback.answer("Заявка не найдена", show_alert=True)
        return
    await state.update_data(task_id=task_id)
    kb = assign_type_keyboard(task_id)
    await callback.message.edit_text(
        f"📋 Выберите способ назначения для заявки #{task_id}:",
        reply_markup=kb
    )
    await callback.answer()

@router.callback_query(F.data.startswith("task_assign_team:"))
async def assign_team_start(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE, UserRole.DIRECTOR):
        await callback.answer("У вас нет прав.", show_alert=True)
        return
    teams = await get_teams_with_members()
    if not teams:
        await callback.answer("Нет доступных команд.", show_alert=True)
        return
    kb = team_selection_keyboard(teams, task_id)
    await callback.message.edit_text(
        f"👥 Выберите команду для заявки #{task_id}:",
        reply_markup=kb
    )
    await callback.answer()

@router.callback_query(F.data.startswith("task_assign_team_confirm:"))
async def assign_team_confirm(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    task_id = int(parts[1])
    team_str = parts[2]
    team = Team(team_str)
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    task = await assign_task_to_team(task_id, team, employee.id)
    if not task:
        await callback.answer("Ошибка назначения", show_alert=True)
        return
    await notify_team(team, f"📢 Заявка #{task_id} назначена на вашу команду.", task_id=task_id)
    await callback.answer(f"✅ Заявка #{task_id} назначена на команду {team.value}")
    await safe_edit_or_reply(callback, f"✅ Заявка #{task_id} назначена на команду {team.value}")
    await callback.message.answer(
        f"📋 Карточка заявки #{task_id}:",
        reply_markup=task_actions_keyboard(task, employee)
    )

@router.callback_query(F.data.startswith("task_assign_user:"))
async def assign_user_start(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE, UserRole.DIRECTOR):
        await callback.answer("У вас нет прав.", show_alert=True)
        return
    employees = await get_available_employees()
    if not employees:
        await callback.answer("Нет доступных сотрудников.", show_alert=True)
        return
    kb = employee_selection_keyboard(employees, task_id, "task_assign_user_confirm")
    await callback.message.edit_text(
        f"👤 Выберите сотрудника для заявки #{task_id}:",
        reply_markup=kb
    )
    await callback.answer()

@router.callback_query(F.data.startswith("task_assign_user_confirm:"))
async def assign_user_confirm(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    task_id = int(parts[1])
    user_id = int(parts[2])
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    task = await assign_task_to_user(task_id, user_id, employee.id)
    if not task:
        await callback.answer("Ошибка назначения", show_alert=True)
        return
    assignee = await get_employee_by_id(user_id)
    if assignee and assignee.telegram_id:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Посмотреть заявку", callback_data=f"task:{task_id}")]
        ])
        await notify_user(
            assignee.telegram_id,
            f"📢 Вам назначена заявка #{task_id}.",
            task_id=task_id,
            reply_markup=keyboard
        )
    await callback.answer(f"✅ Заявка #{task_id} назначена на {assignee.full_name if assignee else 'сотрудника'}")
    await safe_edit_or_reply(callback, f"✅ Заявка #{task_id} назначена на {assignee.full_name if assignee else 'сотрудника'}")
    await callback.message.answer(
        f"📋 Карточка заявки #{task_id}:",
        reply_markup=task_actions_keyboard(task, employee)
    )

# ---------- Передача ----------
@router.callback_query(F.data.startswith("task_transfer:"))
async def transfer_task_start(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Вы не зарегистрированы", show_alert=True)
        return
    task = await get_task(task_id)
    if not task or task.assigned_to != employee.id:
        await callback.answer("Вы не исполнитель этой задачи", show_alert=True)
        return
    employees = await get_available_employees(exclude_id=employee.id)
    if not employees:
        await callback.answer("Нет доступных сотрудников для передачи.", show_alert=True)
        return
    await state.update_data(task_id=task_id)
    kb = employee_selection_keyboard(employees, task_id, "task_transfer_confirm")
    await callback.message.edit_text(
        f"↗️ Выберите сотрудника для передачи заявки #{task_id}:",
        reply_markup=kb
    )
    await callback.answer()

@router.callback_query(F.data.startswith("task_transfer_confirm:"))
async def transfer_task_confirm(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    task_id = int(parts[1])
    to_user_id = int(parts[2])
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    task = await transfer_task(task_id, employee.id, to_user_id, comment="Требуется помощь")
    if not task:
        await callback.answer("Ошибка передачи", show_alert=True)
        return
    new_assignee = await get_employee_by_id(to_user_id)
    if new_assignee and new_assignee.telegram_id:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Посмотреть заявку", callback_data=f"task:{task_id}")]
        ])
        current_user = await get_employee(callback.from_user.id)
        sender_name = current_user.full_name if current_user else "Сотрудник"
        await notify_user(
            new_assignee.telegram_id,
            f"📢 Вам передана задача #{task_id}: {task.title}\nОт: {sender_name}\nКомментарий: Требуется помощь",
            task_id=task_id,
            reply_markup=keyboard
        )
    await callback.answer(f"✅ Заявка #{task_id} передана {new_assignee.full_name if new_assignee else 'сотруднику'}")
    await safe_edit_or_reply(callback, f"✅ Заявка #{task_id} передана {new_assignee.full_name if new_assignee else 'сотруднику'}")
    await callback.message.answer(
        f"📋 Карточка заявки #{task_id}:",
        reply_markup=task_actions_keyboard(task, employee)
    )

# ---------- Отмена ----------
@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("Действие отменено")
