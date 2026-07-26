from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
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
from app.keyboards.main_menu import main_menu_keyboard
from app.states.tasks.transfer import TaskTransfer
from app.services.notification_service import notify_user, notify_team

router = Router()

# ---------- Назначение ----------
@router.callback_query(F.data.startswith("task_assign:"))
async def start_assign(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE, UserRole.DIRECTOR):
        await callback.answer("У вас нет прав для назначения", show_alert=True)
        return
    task = await get_task(task_id)
    if not task:
        await callback.answer("Задача не найдена", show_alert=True)
        return
    await callback.message.edit_text(
        f"Выберите способ назначения для задачи #{task_id}:",
        reply_markup=assign_type_keyboard(task_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("assign_type_team:"))
async def choose_team_for_assign(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    teams = await get_teams_with_members()
    if not teams:
        await callback.message.edit_text("Нет доступных команд. Нажмите «В меню», чтобы вернуться.")
        return
    await callback.message.edit_text(
        f"Выберите команду для задачи #{task_id}:",
        reply_markup=team_selection_keyboard(teams, task_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("assign_team:"))
async def assign_to_team(callback: CallbackQuery):
    _, team_str, task_id_str = callback.data.split(":")
    team = Team(team_str)
    task_id = int(task_id_str)
    admin = await get_employee(callback.from_user.id)
    if not admin:
        await callback.answer("Ошибка", show_alert=True)
        return
    task = await assign_task_to_team(task_id, team, admin.id)
    if not task:
        await callback.answer("Ошибка назначения", show_alert=True)
        return

    # Уведомление команде
        # Отправляем уведомление команде с кнопкой "Взять"
        from app.services.notification_service import notify_team_with_button
        await notify_team_with_button(team, f"📢 Новая задача #{task_id} назначена на вашу команду.\nНазвание: {task.title}", task_id)

    await callback.message.delete()
    await callback.message.answer(
        f"✅ Задача #{task_id} назначена на команду {team.value}.",
        reply_markup=main_menu_keyboard(admin.role)
    )
    await callback.answer("Назначено")


@router.callback_query(F.data.startswith("assign_type_user:"))
async def choose_user_for_assign(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    task = await get_task(task_id)
    if not task:
        await callback.answer("Задача не найдена", show_alert=True)
        return
    employees = await get_available_employees(exclude_id=task.assigned_to)
    if not employees:
        await callback.message.edit_text("Нет доступных сотрудников. Нажмите «В меню», чтобы вернуться.")
        return
    await callback.message.edit_text(
        f"Выберите сотрудника для задачи #{task_id}:",
        reply_markup=employee_selection_keyboard(employees, action="assign", task_id=task_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("assign_emp:"))
async def assign_employee(callback: CallbackQuery):
    _, emp_id_str, task_id_str = callback.data.split(":")
    emp_id = int(emp_id_str)
    task_id = int(task_id_str)
    admin = await get_employee(callback.from_user.id)
    if not admin:
        await callback.answer("Ошибка", show_alert=True)
        return
    task = await assign_task_to_user(task_id, emp_id, admin.id)
    if not task:
        await callback.answer("Ошибка назначения", show_alert=True)
        return
    new_assignee = await get_employee_by_id(emp_id)
    if not new_assignee:
        await callback.answer("Сотрудник не найден", show_alert=True)
        return
    if new_assignee.telegram_id:
        await notify_user(
            new_assignee.telegram_id,
            f"📢 Вам назначена задача #{task_id}: {task.title}\nНазначил: {admin.full_name}"
        )
    await callback.message.delete()
    await callback.message.answer(
        f"✅ Задача #{task_id} назначена на {new_assignee.full_name}.",
        reply_markup=main_menu_keyboard(admin.role)
    )
    await callback.answer("Назначено")


# ---------- Возврат к выбору типа назначения ----------
@router.callback_query(F.data.startswith("assign_back_to_type:"))
async def back_to_assign_type(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        f"Выберите способ назначения для задачи #{task_id}:",
        reply_markup=assign_type_keyboard(task_id)
    )
    await callback.answer()


# ---------- Пропуск назначения (в меню) ----------
@router.callback_query(F.data.startswith("assign_skip:"))
async def skip_assign(callback: CallbackQuery):
    employee = await get_employee(callback.from_user.id)
    await callback.message.delete()
    if employee:
        await callback.message.answer("Назначение пропущено.", reply_markup=main_menu_keyboard(employee.role))
    else:
        await callback.message.answer("Назначение пропущено.")
    await callback.answer()


# ---------- Передача задачи (исполнитель -> другому) ----------
@router.callback_query(F.data.startswith("task_transfer:"))
async def start_transfer(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Вы не зарегистрированы", show_alert=True)
        return
    task = await get_task(task_id)
    if not task or task.assigned_to != employee.id:
        await callback.answer("Вы не являетесь исполнителем этой задачи", show_alert=True)
        return
    employees = await get_available_employees(exclude_id=employee.id)
    if not employees:
        await callback.message.answer("Нет доступных сотрудников для передачи.")
        return
    await callback.message.answer(
        f"Выберите сотрудника для передачи задачи #{task_id}:",
        reply_markup=employee_selection_keyboard(employees, action="transfer", task_id=task_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("transfer_emp:"))
async def select_transfer_employee(callback: CallbackQuery, state: FSMContext):
    _, emp_id_str, task_id_str = callback.data.split(":")
    emp_id = int(emp_id_str)
    task_id = int(task_id_str)
    await state.update_data(to_employee_id=emp_id, task_id=task_id)
    await state.set_state(TaskTransfer.comment)
    await callback.message.edit_text("✍️ Введите комментарий для передачи (или '-' для пропуска):")
    await callback.answer()


@router.message(TaskTransfer.comment)
async def process_transfer_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    task_id = data.get("task_id")
    to_emp_id = data.get("to_employee_id")
    from_emp = await get_employee(message.from_user.id)
    if not from_emp:
        await message.answer("Ошибка")
        await state.clear()
        return
    comment = message.text.strip()
    if comment == "-":
        comment = None
    task = await transfer_task(task_id, from_emp.id, to_emp_id, comment)
    if not task:
        await message.answer("❌ Ошибка передачи задачи")
        await state.clear()
        return
    new_assignee = await get_employee_by_id(to_emp_id)
    if new_assignee and new_assignee.telegram_id:
        await notify_user(
            new_assignee.telegram_id,
            f"📢 Вам передана задача #{task_id}: {task.title}\n"
            f"От: {from_emp.full_name}\n"
            f"Комментарий: {comment or 'без комментария'}"
        )
    await message.answer(
        f"✅ Задача #{task_id} передана {new_assignee.full_name}.",
        reply_markup=main_menu_keyboard(from_emp.role)
    )
    await state.clear()


@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("Действие отменено")
# (добавим импорт InlineKeyboardButton в начале файла, если нет)
