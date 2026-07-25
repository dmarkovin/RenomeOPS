from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.types import Message

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup
from aiogram.fsm.state import State

from app.database import database
from app.services.task_history_service import add_history

router = Router()


class CloseTaskState(StatesGroup):

    report = State()


@router.callback_query(
    lambda c: c.data.startswith("close:")
)
async def close_task_start(
    callback: CallbackQuery,
    state: FSMContext
):

    task_id = int(callback.data.split(":")[1])

    await state.update_data(task_id=task_id)

    await state.set_state(CloseTaskState.report)

    await callback.message.edit_text(
        """
✅ Завершение заявки

Опишите,

что было выполнено.

Этот отчет увидит консьерж.
"""
    )

    await callback.answer()
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton

from app.services.notification_service import notify_task_check


@router.message(CloseTaskState.report)
async def close_task_finish(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    task_id = data["task_id"]

    report = message.text

    task = await database.fetchrow(
        """
        SELECT

            id,

            title,

            concierge_id

        FROM tasks

        WHERE id=$1
        """,
        task_id
    )

    if not task:

        await message.answer("Заявка не найдена.")

        await state.clear()

        return

    await database.execute(
        """
        UPDATE tasks

        SET

            status='CHECKING',

            report=$1,

            updated_at=NOW()

        WHERE id=$2
        """,
        report,
        task_id
    )

    await add_history(

        task_id=task_id,

        employee_id=message.from_user.id,

        action="CHECKING",

        comment=report

    )

    if task["concierge_id"]:

        await notify_task_check(

            telegram_id=task["concierge_id"],

            task_id=task_id,

            title=task["title"]

        )

    await state.clear()

    await message.answer(

        """
✅ Работа завершена.

Заявка отправлена консьержу на проверку.
"""

    )


@router.callback_query(
    lambda c: c.data == "ignore"
)
async def ignore(callback: CallbackQuery):

    await callback.answer()
