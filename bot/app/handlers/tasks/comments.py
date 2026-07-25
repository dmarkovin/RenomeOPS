from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from app.database import database
from app.services.task_history_service import add_history

router = Router()


class CommentState(StatesGroup):

    text = State()


@router.callback_query(lambda c: c.data.startswith("comments:"))
async def comment_start(
    callback: CallbackQuery,
    state: FSMContext
):

    task_id = int(callback.data.split(":")[1])

    await state.update_data(task_id=task_id)

    await state.set_state(CommentState.text)

    await callback.message.edit_text(
        """
💬 Новый комментарий

Введите текст комментария.
"""
    )

    await callback.answer()
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton


@router.message(CommentState.text)
async def comment_save(
    message,
    state: FSMContext
):

    data = await state.get_data()

    task_id = data["task_id"]

    comment = message.text

    await database.execute(
        """
        INSERT INTO task_comments(

            task_id,

            employee_id,

            comment,

            created_at

        )

        VALUES(

            $1,

            $2,

            $3,

            NOW()

        )
        """,

        task_id,

        message.from_user.id,

        comment

    )

    await add_history(

        task_id=task_id,

        employee_id=message.from_user.id,

        action="COMMENT",

        comment=comment

    )

    await state.clear()

    keyboard = InlineKeyboardMarkup(

        inline_keyboard=[

            [

                InlineKeyboardButton(

                    text="📋 Вернуться к заявке",

                    callback_data=f"task_card:{task_id}"

                )

            ]

        ]

    )

    await message.answer(

        """
✅ Комментарий сохранён.
""",

        reply_markup=keyboard

    )


@router.callback_query(lambda c: c.data.startswith("show_comments:"))
async def show_comments(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    comments = await database.fetch(
        """
        SELECT

            tc.comment,

            tc.created_at,

            e.full_name

        FROM task_comments tc

        LEFT JOIN employees e

            ON e.id = tc.employee_id

        WHERE tc.task_id=$1

        ORDER BY tc.created_at DESC
        """,

        task_id

    )

    if not comments:

        await callback.answer(
            "Комментариев пока нет",
            show_alert=True
        )

        return

    text = f"<b>💬 Комментарии заявки №{task_id}</b>\n\n"

    for row in comments:

        text += (
            f"👤 {row['full_name']}\n"
            f"🕒 {row['created_at']}\n"
            f"{row['comment']}\n\n"
        )

    keyboard = InlineKeyboardMarkup(

        inline_keyboard=[

            [

                InlineKeyboardButton(

                    text="⬅ Назад",

                    callback_data=f"task_card:{task_id}"

                )

            ]

        ]

    )

    await callback.message.edit_text(

        text,

        reply_markup=keyboard

    )

    await callback.answer()
