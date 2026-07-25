from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton

from app.database import database
from app.services.task_history_service import add_history

router = Router()


@router.callback_query(
    lambda c: c.data.startswith("check_task:")
)
async def open_check_panel(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    task = await database.fetchrow(
        """
        SELECT

            id,

            title,

            report

        FROM tasks

        WHERE id=$1
        """,
        task_id
    )

    if not task:

        await callback.answer(
            "Заявка не найдена",
            show_alert=True
        )
        return

    keyboard = InlineKeyboardMarkup(

        inline_keyboard=[

            [

                InlineKeyboardButton(

                    text="✔ Принять",

                    callback_data=f"approve_task:{task_id}"

                )

            ],

            [

                InlineKeyboardButton(

                    text="↩ Вернуть",

                    callback_data=f"reject_task:{task_id}"

                )

            ]

        ]

    )

    await callback.message.edit_text(

        f"""
📋 Проверка заявки

<b>{task['title']}</b>

Отчет исполнителя:

{task['report'] or '—'}
""",

        reply_markup=keyboard

    )

    await callback.answer()
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.services.notification_service import notify_task_return


class RejectState(StatesGroup):
    comment = State()


# ==========================
# Принять заявку
# ==========================

@router.callback_query(
    lambda c: c.data.startswith("approve_task:")
)
async def approve_task(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    task = await database.fetchrow(
        """
        SELECT

            executor_id

        FROM tasks

        WHERE id=$1
        """,
        task_id
    )

    await database.execute(
        """
        UPDATE tasks

        SET

            status='CLOSED',

            closed_at=NOW(),

            updated_at=NOW()

        WHERE id=$1
        """,
        task_id
    )

    await add_history(

        task_id=task_id,

        employee_id=callback.from_user.id,

        action="APPROVED",

        comment="Работа принята"

    )

    await callback.message.edit_text(
        f"""
✅ Заявка №{task_id}

успешно закрыта.
"""
    )

    await callback.answer()


# ==========================
# Вернуть исполнителю
# ==========================

@router.callback_query(
    lambda c: c.data.startswith("reject_task:")
)
async def reject_task(
    callback: CallbackQuery,
    state: FSMContext
):

    task_id = int(callback.data.split(":")[1])

    await state.update_data(task_id=task_id)

    await state.set_state(RejectState.comment)

    await callback.message.edit_text(
        """
↩ Возврат заявки

Напишите комментарий,

что необходимо исправить.
"""
    )

    await callback.answer()


@router.message(RejectState.comment)
async def reject_finish(
    message,
    state: FSMContext
):

    data = await state.get_data()

    task_id = data["task_id"]

    comment = message.text

    task = await database.fetchrow(
        """
        SELECT

            executor_id

        FROM tasks

        WHERE id=$1
        """,
        task_id
    )

    await database.execute(
        """
        UPDATE tasks

        SET

            status='IN_PROGRESS',

            updated_at=NOW()

        WHERE id=$1
        """,
        task_id
    )

    await add_history(

        task_id=task_id,

        employee_id=message.from_user.id,

        action="REJECT",

        comment=comment

    )

    if task["executor_id"]:

        await notify_task_return(

            telegram_id=task["executor_id"],

            task_id=task_id,

            comment=comment

        )

    await state.clear()

    await message.answer(
        """
↩ Заявка возвращена исполнителю.
"""
    )
