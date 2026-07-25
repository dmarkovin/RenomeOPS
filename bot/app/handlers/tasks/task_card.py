from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton

from app.database import database

router = Router()


@router.callback_query(
    lambda c: c.data.startswith("task_card:")
)
async def open_task_card(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    task = await database.fetchrow(
        """
        SELECT

            t.id,

            t.title,

            t.status,

            t.priority,

            t.building,

            t.apartment,

            t.created_at,

            creator.full_name AS creator,

            executor.full_name AS executor

        FROM tasks t

        LEFT JOIN employees creator

            ON creator.id=t.created_by

        LEFT JOIN employees executor

            ON executor.id=t.executor_id

        WHERE t.id=$1
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
                    text="👤 Назначить",
                    callback_data=f"assign:{task_id}"
                ),
                InlineKeyboardButton(
                    text="🔄 Передать",
                    callback_data=f"transfer:{task_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💬 Комментарии",
                    callback_data=f"show_comments:{task_id}"
                ),
                InlineKeyboardButton(
                    text="📷 Фото",
                    callback_data=f"show_photos:{task_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📜 История",
                    callback_data=f"history:{task_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="✅ Завершить",
                    callback_data=f"close:{task_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔙 К списку заявок",
                    callback_data="tasks_menu"
                )
            ]
        ]
    )

    status_names = {
        "CREATED": "🆕 Новая",
        "ASSIGNED": "👤 Назначена",
        "IN_PROGRESS": "🚧 В работе",
        "CHECKING": "🔎 Проверка",
        "CLOSED": "✅ Закрыта"
    }

    priority_names = {
        1: "🟢 Низкий",
        2: "🟢 Обычный",
        3: "🟡 Средний",
        4: "🟠 Высокий",
        5: "🔴 Авария"
    }

    text = f"""
<b>📋 Заявка №{task['id']}</b>

<b>{task['title']}</b>

━━━━━━━━━━━━━━━━━━

<b>Статус:</b>
{status_names.get(task["status"], task["status"])}

<b>Приоритет:</b>
{priority_names.get(task["priority"], task["priority"])}

<b>Исполнитель:</b>
{task["executor"] or "Не назначен"}

<b>Создал:</b>
{task["creator"]}

<b>Здание:</b>
{task["building"] or "—"}

<b>Квартира:</b>
{task["apartment"] or "—"}

━━━━━━━━━━━━━━━━━━

Дата создания:

{task["created_at"]}
"""

    await callback.message.edit_text(
        text,
        reply_markup=keyboard
    )

    await callback.answer()
