from aiogram import Router
from aiogram.types import CallbackQuery

from app.services.task_history_service import get_history

router = Router()


@router.callback_query(
    lambda c: c.data.startswith("history:")
)
async def show_history(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    history = await get_history(task_id)

    if not history:

        await callback.answer(
            "История пуста",
            show_alert=True
        )

        return

    text = f"<b>📜 История заявки №{task_id}</b>\n\n"

    for row in history:

        text += (
            f"🕒 {row['created_at']}\n"
            f"👤 {row['full_name'] or 'Система'}\n"
            f"📌 {row['action']}\n"
        )

        if row["comment"]:
            text += f"💬 {row['comment']}\n"

        text += "\n"

    await callback.message.edit_text(text)

    await callback.answer()
