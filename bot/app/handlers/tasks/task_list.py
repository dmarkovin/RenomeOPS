from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from app.services.tasks.service import get_open_tasks

router = Router()


@router.message(F.text == "📋 Заявки")
async def task_list(message: Message):

    tasks = await get_open_tasks()

    if not tasks:

        await message.answer(
            "Открытых заявок нет."
        )
        return

    for task in tasks:

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📂 Открыть",
                        callback_data=f"card:{task['id']}"
                    )
                ]
            ]
        )

        await message.answer(

            f"""
📋 Заявка №{task['id']}

🏷 {task['title']}

Статус:
{task['status']}

Приоритет:
{task['priority']}
""",

            reply_markup=kb

        )
