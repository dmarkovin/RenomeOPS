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
from app.services.tasks.service import assign_task_to_user
from app.services.employees.service import get_employee

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
    admin = await get_employee(callback.from_user.id)
    if not admin:
        await callback.answer("Ошибка", show_alert=True)
        return
    # Используем сервисную функцию с force=True, чтобы разрешить назначение любого сотрудника
    task = await assign_task_to_user(task_id, employee_id, admin.id, force=True)
    if not task:
        await callback.answer("Не удалось назначить задачу", show_alert=True)
        return
    # Получаем назначенного сотрудника для отображения
    from app.services.employees.service import get_employee_by_id
    employee = await get_employee_by_id(employee_id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    await callback.message.edit_text(
        f"""
✅ Исполнитель назначен

Заявка №{task.id}
Исполнитель:
<b>{employee.full_name}</b>
"""
    )
    await callback.answer("Готово")
