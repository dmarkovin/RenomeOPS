from aiogram import Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.database import database

router = Router()


class TransferState(StatesGroup):
    comment = State()


@router.callback_query(lambda c: c.data.startswith("transfer:"))
async def transfer_task(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    employees = await database.fetch(
        """
        SELECT

            id,

            full_name,

            team

        FROM employees

        WHERE is_active = TRUE

        ORDER BY team, full_name
        """
    )

    keyboard = []

    current_team = None

    for employee in employees:

        if current_team != employee["team"]:

            current_team = employee["team"]

            keyboard.append([
                InlineKeyboardButton(
                    text=f"──── {current_team} ────",
                    callback_data="ignore"
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                text=employee["full_name"],
                callback_data=f"transfer_to:{task_id}:{employee['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="⬅ Назад",
            callback_data=f"task_card:{task_id}"
        )
    ])

    await callback.message.edit_text(
        "Выберите нового исполнителя",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )

    await callback.answer()
from app.services.notification_service import notify_new_task
from app.services.task_history_service import add_history


@router.callback_query(lambda c: c.data.startswith("transfer_to:"))
async def transfer_select_employee(
    callback: CallbackQuery,
    state: FSMContext
):

    _, task_id, employee_id = callback.data.split(":")

    await state.update_data(

        task_id=int(task_id),

        employee_id=int(employee_id)

    )

    await state.set_state(TransferState.comment)

    await callback.message.edit_text(
        """
💬 Перед передачей заявки необходимо указать комментарий.

Напишите причину передачи заявки.
"""
    )

    await callback.answer()


@router.message(TransferState.comment)
async def transfer_finish(
    message,
    state: FSMContext
):

    data = await state.get_data()

    task_id = data["task_id"]

    employee_id = data["employee_id"]

    comment = message.text

    employee = await database.fetchrow(
        """
        SELECT

            id,

            full_name,

            telegram_id

        FROM employees

        WHERE id=$1
        """,
        employee_id
    )

    task = await database.fetchrow(
        """
        SELECT

            id,

            title,

            priority

        FROM tasks

        WHERE id=$1
        """,
        task_id
    )

    await database.execute(
        """
        UPDATE tasks

        SET

            executor_id=$1,

            updated_at=NOW()

        WHERE id=$2
        """,
        employee_id,
        task_id
    )

    await add_history(

        task_id=task_id,

        employee_id=message.from_user.id,

        action="TRANSFER",

        comment=f"{comment}\n\nПередано: {employee['full_name']}"

    )

    if employee["telegram_id"]:

        await notify_new_task(

            telegram_id=employee["telegram_id"],

            task_id=task_id,

            title=task["title"],

            priority=task["priority"]

        )

    await state.clear()

    await message.answer(
        f"""
✅ Заявка успешно передана.

👤 Новый исполнитель:

{employee['full_name']}
"""
    )
