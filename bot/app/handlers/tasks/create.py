from aiogram import Router
from aiogram import F

router = Router()


@router.message(F.text == "➕ Создать заявку")
async def create_task_start(message):

    await message.answer(
        "🚧 Модуль создания заявки подключён.\n\nСледующим шагом сделаем мастер создания заявки."
    )
