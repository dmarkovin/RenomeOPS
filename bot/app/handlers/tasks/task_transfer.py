from aiogram import Router
from aiogram.types import (
    CallbackQuery,
    Message
)
from aiogram.fsm.context import FSMContext

from app.states.tasks.transfer import TransferTask

from app.services.tasks.service import (
    get_task,
    assign_task
)

from app.services.tasks.history import add_history

from app.services.employee_service import (
    get_employee,
    get_employee_by_id,
    get_team_members
)

from app.services.notifications.service import (
    notify_transfer
)

from app.keyboards.tasks.transfer import (
    transfer_keyboard
)

router = Router()


# =====================================================
# Выбор сотрудника
# =====================================================

@router.callback_query(
    lambda c: c.data.startswith("transfer:")
)
async def transfer_choose_employee(
    callback: CallbackQuery,
    state: FSMContext
):

    task_id = int(
        callback.data.split(":")[1]
    )

    task = await get_task(
        task_id
    )

    if not task:

        await callback.answer(
            "Заявка не найдена.",
            show_alert=True
        )

        return

    current_employee = await get_employee(
        callback.from_user.id
    )

    if not current_employee:

        await callback.answer(
            "Вы не зарегистрированы.",
            show_alert=True
        )

        return

    team = current_employee["team"]

    employees = await get_team_members(
        team
    )

    employees = [

        employee

        for employee in employees

        if employee["telegram_id"] != callback.from_user.id

    ]

    if not employees:

        await callback.answer(
            "Некому передать заявку.",
            show_alert=True
        )

        return

    await state.update_data(

        task_id=task_id,

        current_employee=current_employee["id"]

    )

    await callback.message.edit_text(

        f"""
↔ Передача заявки

№ {task_id}

Выберите сотрудника.
""",

        reply_markup=transfer_keyboard(
            employees
        )

    )


# =====================================================
# Выбран сотрудник
# =====================================================

@router.callback_query(
    lambda c: c.data.startswith(
        "transfer_to:"
    )
)
async def transfer_selected(
    callback: CallbackQuery,
    state: FSMContext
):

    employee_id = int(
        callback.data.split(":")[1]
    )

    data = await state.get_data()

    await state.update_data(

        new_employee=employee_id

    )

    await state.set_state(
        TransferTask.comment
    )

    employee = await get_employee_by_id(
        employee_id
    )

    await callback.message.edit_text(

        f"""
Вы выбрали:

👤 {employee['full_name']}

Теперь отправьте комментарий.

Например:

Требуется помощь с электрикой.
"""

    )
# =====================================================
# Получение комментария
# =====================================================

@router.message(
    TransferTask.comment
)
async def transfer_comment(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    task_id = data["task_id"]

    new_employee_id = data["new_employee"]

    current_employee = data["current_employee"]

    employee = await get_employee_by_id(
        new_employee_id
    )

    # =======================================
    # Меняем исполнителя
    # =======================================

    await assign_task(

        task_id,

        new_employee_id

    )

    # =======================================
    # История
    # =======================================

    await add_history(

        task_id=task_id,

        employee_id=current_employee,

        action="TRANSFER",

        comment=f"""
Передано:

{employee['full_name']}

Комментарий:

{message.text}
"""

    )

    # =======================================
    # Уведомление новому исполнителю
    # =======================================

    if employee["telegram_id"]:

        await notify_transfer(

            telegram_id=employee["telegram_id"],

            task_id=task_id,

            comment=message.text

        )

    await state.clear()

    await message.answer(

        f"""
✅ Заявка №{task_id}

успешно передана

👤 {employee['full_name']}

Комментарий сохранён.
"""

    )


# =====================================================
# Отмена передачи
# =====================================================

@router.callback_query(
    lambda c: c.data == "transfer_cancel"
)
async def transfer_cancel(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.clear()

    await callback.answer()

    await callback.message.edit_text(

        """
❌ Передача заявки отменена.
"""

    )
