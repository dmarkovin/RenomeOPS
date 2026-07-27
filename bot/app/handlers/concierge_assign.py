from aiogram.types import ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton

from sqlalchemy import select

from app.database.models import Task
from app.database.models import TaskStatus
from app.database.models import User


router = Router()


@router.callback_query(
    lambda c: c.data.startswith("assign:")
)
async def choose_employee(
    callback: CallbackQuery,
    session: AsyncSession
):
    task_id = int(
        callback.data.split(":")[1]
    )


    employees = (
        await session.execute(
            select(User)
            .where(
                User.active == True
            )
        )
    ).scalars().all()


    keyboard = []


    for employee in employees:

        keyboard.append(
            [
                InlineKeyboardButton(
                    text=employee.full_name,
                    callback_data=
                    f"assign_to:{task_id}:{employee.id}"
                )
            ]
        )


    await callback.message.edit_text(

        "Выберите исполнителя:",

        reply_markup=
        InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )

    )

    await callback.answer()



@router.callback_query(
    lambda c: c.data.startswith("assign_to:")
)
async def assign_employee(
    callback: CallbackQuery,
    session: AsyncSession
):
    _, task_id, employee_id = callback.data.split(":")


    task_id = int(task_id)

    employee_id = int(employee_id)



    task = (
        await session.execute(
            select(Task)
            .where(
                Task.id == task_id
            )
        )
    ).scalar_one_or_none()



    employee = (
        await session.execute(
            select(User)
            .where(
                User.id == employee_id
            )
        )
    ).scalar_one_or_none()



    if not task:

        await callback.answer(
            "Заявка не найдена",
            show_alert=True
        )

        return



    task.assigned_to = employee.id

    task.status = TaskStatus.ACCEPTED



    await session.commit()



    await callback.message.edit_text(

        f"""
✅ Исполнитель назначен


Заявка №{task.id}

Исполнитель:

<b>{employee.full_name}</b>
"""

    )


    await callback.answer(
        "Готово"
    )
