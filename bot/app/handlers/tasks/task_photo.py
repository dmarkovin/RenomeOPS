from aiogram import Router
from aiogram.types import (
    CallbackQuery,
    Message
)
from aiogram.fsm.context import FSMContext

from app.services.tasks.service import (
    get_task
)

from app.services.tasks.history import (
    add_history
)

router = Router()


# =====================================================
# Начало фотоотчета
# =====================================================

@router.callback_query(
    lambda c: c.data.startswith("photo:")
)
async def photo_start(
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
            "Заявка не найдена",
            show_alert=True
        )

        return

    await state.update_data(

        task_id=task_id,

        photos=[]

    )

    await callback.answer()

    await callback.message.answer(

"""
📷 Фотоотчет

Можно отправить любое количество фотографий.

Когда закончите —

напишите

ГОТОВО
"""

    )


# =====================================================
# Прием фотографий
# =====================================================

@router.message(
    lambda message: message.photo
)
async def receive_photo(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    if "photos" not in data:
        return

    photos = data["photos"]

    file_id = message.photo[-1].file_id

    photos.append(file_id)

    await state.update_data(
        photos=photos
    )

    await message.answer(

f"""
Фото сохранено.

Всего фотографий:

{len(photos)}
"""

    )
# =====================================================
# Завершение фотоотчета
# =====================================================

@router.message()
async def finish_photo_report(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    # Если сейчас не идет фотоотчет —
    # выходим и не мешаем другим хендлерам

    if "photos" not in data:
        return

    if message.text is None:
        return

    if message.text.upper() != "ГОТОВО":

        await message.answer(
            "Продолжайте отправлять фотографии или напишите ГОТОВО."
        )

        return

    task_id = data["task_id"]

    photos = data["photos"]

    # ==========================================
    # Пока сохраняем file_id в историю.
    # Позже вынесем в отдельную таблицу task_files
    # ==========================================

    if photos:

        await add_history(

            task_id=task_id,

            employee_id=message.from_user.id,

            action="PHOTO_REPORT",

            comment="\n".join(photos)

        )

    await state.clear()

    await message.answer(

        f"""
✅ Фотоотчет завершен

Заявка № {task_id}

Получено фотографий:

{len(photos)}

Консьерж и директор смогут открыть фотографии прямо в Telegram.
"""

    )


# =====================================================
# Просмотр фото (заглушка)
# =====================================================

@router.callback_query(
    lambda c: c.data.startswith("photos:")
)
async def open_photo_report(
    callback: CallbackQuery
):

    task_id = int(
        callback.data.split(":")[1]
    )

    await callback.answer()

    await callback.message.answer(

f"""
📷 Фотоотчет

Заявка № {task_id}

На следующем этапе фотографии будут автоматически выгружаться из истории
и отправляться одним сообщением.

Храниться будут только Telegram file_id.
"""

    )
