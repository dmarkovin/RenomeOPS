from aiogram import Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from app.database import database
from app.services.notification_service import notify_new_task
from app.services.task_history_service import add_history

router = Router()


@router.callback_query(lambda c: c.data.startswith("assign:"))
async def assign_task(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    employees = await database.fetch(
        """
        SELECT

            id,

            full_name,

            telegram_id,

            team

        FROM employees

        WHERE is_active = TRUE

        ORDER BY team, full_name
        """
    )

    if not employees:

        await callback.answer(
            "Нет доступных сотрудников",
            show_alert=True,
        )
        return

    keyboard = []

    current_team = None

    team_names = {
        "TEAM_TECH": "🔧 Техническая служба",
        "TEAM_CLEANING": "🧹 Клининг",
        "TEAM_SECURITY": "🛡 Служба безопасности",
    }

    for employee in employees:

        if employee["team"] != current_team:

            current_team = employee["team"]

            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=team_names.get(
                            current_team,
                            current_team,
                        ),
                        callback_data="ignore",
                    )
                ]
            )

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=employee["full_name"],
                    callback_data=f"assign_to:{task_id}:{employee['id']}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="⬅ Назад",
                callback_data=f"task_card:{task_id}",
            )
        ]
    )

    await callback.message.edit_text(
        "👤 Выберите исполнителя",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        ),
    )

    await callback.answer()
@router.callback_query(lambda c: c.data.startswith("assign_to:"))
async def assign_to_employee(callback: CallbackQuery):

    _, task_id, employee_id = callback.data.split(":")

    task_id = int(task_id)
    employee_id = int(employee_id)

    employee = await database.fetchrow(
        """
        SELECT

            id,

            full_name,

            telegram_id

        FROM employees

        WHERE id = $1
        """,
        employee_id,
    )

    if not employee:

        await callback.answer(
            "Исполнитель не найден",
            show_alert=True,
        )
        return

    task = await database.fetchrow(
        """
        SELECT

            id,

            title,

            priority

        FROM tasks

        WHERE id = $1
        """,
        task_id,
    )

    if not task:

        await callback.answer(
            "Заявка не найдена",
            show_alert=True,
        )
        return

    await database.execute(
        """
        UPDATE tasks

        SET

            executor_id = $1,

            status = 'ASSIGNED',

            updated_at = NOW()

        WHERE id = $2
        """,
        employee_id,
        task_id,
    )

    await add_history(

        task_id=task_id,

        employee_id=callback.from_user.id,

        action="ASSIGNED",

        comment=f"Назначено исполнителю: {employee['full_name']}",

    )

    if employee["telegram_id"]:

        await notify_new_task(

            telegram_id=employee["telegram_id"],

            task_id=task_id,

            title=task["title"],

            priority=task["priority"],

        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Открыть заявку",
                    callback_data=f"task_card:{task_id}",
                )
            ]
        ]
    )

    await callback.message.edit_text(
        f"""
✅ <b>Исполнитель назначен</b>

👤 {employee['full_name']}

Заявка №{task_id}
""",
        reply_markup=keyboard,
    )

    await callback.answer()


@router.callback_query(lambda c: c.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    await callback.answer()
