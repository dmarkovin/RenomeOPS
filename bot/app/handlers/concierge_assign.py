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

    # Получаем задачу, чтобы узнать команду (если есть)
    task = (
        await session.execute(
            select(Task).where(Task.id == task_id)
        )
    ).scalar_one_or_none()

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
        # Если у задачи есть assigned_team, фильтруем
        if task and task.assigned_team and employee.team != task.assigned_team:
            continue
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=employee.full_name,
                    callback_data=
                    f"assign_to:{task_id}:{employee.id}"
                )
            ]
        )

    if not keyboard:
        await callback.message.edit_text("Нет доступных сотрудников для назначения.")
        await callback.answer()
        return

    await callback.message.edit_text(
        "Выберите исполнителя:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
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

    # Используем блокировку строки, чтобы избежать race condition
    async with session.begin():
        task = (
            await session.execute(
                select(Task)
                .where(Task.id == task_id)
                .with_for_update()
            )
        ).scalar_one_or_none()

        if not task:
            await callback.answer("Заявка не найдена", show_alert=True)
            return

        # Проверяем, что задача может быть назначена
        if task.status not in ("created", "waiting"):
            await callback.answer(
                f"Задача уже в статусе {task.status} и не может быть назначена",
                show_alert=True
            )
            return

        employee = (
            await session.execute(
                select(User)
                .where(User.id == employee_id)
            )
        ).scalar_one_or_none()

        if not employee or not employee.active:
            await callback.answer("Сотрудник не активен", show_alert=True)
            return

        # Проверяем команду, если задана
        if task.assigned_team and employee.team != task.assigned_team:
            await callback.answer(
                "Сотрудник не из нужной команды",
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
    await callback.answer("Готово")
