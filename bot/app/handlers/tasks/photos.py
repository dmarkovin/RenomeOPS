from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.types import Message

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup
from aiogram.fsm.state import State

from app.database import database
from app.services.task_history_service import add_history

router = Router()


class PhotoState(StatesGroup):

    upload = State()


@router.callback_query(lambda c: c.data.startswith("photos:"))
async def add_photo_start(

    callback: CallbackQuery,

    state: FSMContext

):

    task_id = int(callback.data.split(":")[1])

    await state.update_data(task_id=task_id)

    await state.set_state(PhotoState.upload)

    await callback.message.edit_text(
        """
📷 Загрузка фотографии

Отправьте фотографию.

Можно отправлять оригинал или сжатое фото.
"""
    )

    await callback.answer()
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton


@router.message(PhotoState.upload)
async def upload_photo(
    message: Message,
    state: FSMContext
):

    if not message.photo:

        await message.answer(
            "Пожалуйста, отправьте фотографию."
        )
        return

    data = await state.get_data()

    task_id = data["task_id"]

    file_id = message.photo[-1].file_id

    await database.execute(
        """
        INSERT INTO task_photos(

            task_id,

            employee_id,

            telegram_file_id,

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

        file_id

    )

    await add_history(

        task_id=task_id,

        employee_id=message.from_user.id,

        action="PHOTO",

        comment="Добавлена фотография"

    )

    keyboard = InlineKeyboardMarkup(

        inline_keyboard=[

            [

                InlineKeyboardButton(

                    text="➕ Добавить ещё",

                    callback_data=f"photos:{task_id}"

                )

            ],

            [

                InlineKeyboardButton(

                    text="📷 Просмотреть",

                    callback_data=f"show_photos:{task_id}"

                )

            ],

            [

                InlineKeyboardButton(

                    text="✅ Готово",

                    callback_data=f"task_card:{task_id}"

                )

            ]

        ]

    )

    await state.clear()

    await message.answer(

        "✅ Фотография сохранена.",

        reply_markup=keyboard

    )


@router.callback_query(
    lambda c: c.data.startswith("show_photos:")
)
async def show_photos(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    photos = await database.fetch(
        """
        SELECT

            telegram_file_id

        FROM task_photos

        WHERE task_id=$1

        ORDER BY created_at
        """,

        task_id

    )

    if not photos:

        await callback.answer(
            "Фотографий нет",
            show_alert=True
        )
        return

    await callback.answer()

    for photo in photos:

        await callback.message.answer_photo(
            photo["telegram_file_id"]
        )

    await callback.message.answer(

        "Все фотографии заявки показаны.",

        reply_markup=InlineKeyboardMarkup(

            inline_keyboard=[

                [

                    InlineKeyboardButton(

                        text="⬅ Назад",

                        callback_data=f"task_card:{task_id}"

                    )

                ]

            ]

        )

    )
