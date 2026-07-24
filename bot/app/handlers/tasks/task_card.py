from aiogram import Router
from aiogram.types import CallbackQuery

from app.services.tasks.service import get_task

from app.keyboards.tasks.task_card import task_card_keyboard

router = Router()


ROLE = "CONCIERGE"


@router.callback_query(lambda c: c.data.startswith("card:"))
async def open_card(callback: CallbackQuery):

    task_id = int(
        callback.data.split(":")[1]
    )

    task = await get_task(task_id)

    if not task:

        await callback.answer(
            "Заявка не найдена",
            show_alert=True
        )

        return

    await callback.message.edit_text(

        f"""
📋 Заявка №{task['id']}

Название:
{task['title']}

Описание:
{task['description']}

Статус:
{task['status']}

Приоритет:
{task['priority']}
""",

        reply_markup=task_card_keyboard(

            ROLE,

            task["status"],

            task["id"]

        )

    )
