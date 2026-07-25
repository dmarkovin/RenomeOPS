from aiogram import Router
from aiogram.types import CallbackQuery

from app.services.tasks.service import (
    get_task,
    assign_task
)

from app.services.tasks.history import add_history

from app.services.employee_service import (
    get_team_members,
    get_employee_by_id
)

from app.services.notifications.service import (
    notify_new_task
)

from app.keyboards.tasks.assign import (
    assign_keyboard
)

router = Router()


# ============================================================
# Категория → Команда
# ============================================================

CATEGORY_TEAM = {

    "🚰 Сантехника": "TEAM_TECH",

    "💡 Электрика": "TEAM_TECH",

    "🔧 Техническая": "TEAM_TECH",

    "🧹 Клининг": "TEAM_CLEANING",

    "🛡 Безопасность": "TEAM_SECURITY",

    "🏢 Административная": "ADMINISTRATION",

    "📦 Другое": "TEAM_TECH",

}


# ============================================================
# Выбор исполнителя
# ============================================================

@router.callback_query(lambda c: c.data.startswith("assign:"))
async def choose_employee(callback: CallbackQuery):

    task_id = int(
        callback.data.split(":")[1]
    )

    task = await get_task(task_id)

    if not task:

        await callback.answer(
            "Заявка не найдена.",
            show_alert=True
        )

        return

    team = CATEGORY_TEAM.get(
        task["category"],
        "TEAM_TECH"
    )

    employees = await get_team_members(team)

    if not employees:

        await callback.answer(
            "Нет сотрудников этой команды.",
            show_alert=True
        )

        return

    await callback.message.edit_text(

        f"""
👤 Назначение исполнителя

Заявка №{task['id']}

🏷 {task['title']}

Команда:

{team}
""",

        reply_markup=assign_keyboard(
            employees
        )

    )


# ============================================================
# Назначить сотрудника
# ============================================================

@router.callback_query(lambda c: c.data.startswith("assign_employee:"))
async def assign_employee(callback: CallbackQuery):

    employee_id = int(
        callback.data.split(":")[1]
    )

    task_id = int(
        callback.message.text.split("№")[1].split("\n")[0]
    )

    task = await get_task(task_id)

    employee = await get_employee_by_id(
        employee_id
    )

    if not employee:

        await callback.answer(
            "Сотрудник не найден.",
            show_alert=True
        )

        return

    await assign_task(

        task_id,

        employee_id

    )

    await add_history(

        task_id=task_id,

        employee_id=callback.from_user.id,

        action="ASSIGN",

        comment=f"Назначен {employee['full_name']}"

    )

    # =====================================================
    # Отправляем уведомление исполнителю
    # =====================================================

    if employee["telegram_id"]:

        await notify_new_task(

            employee["telegram_id"],

            task_id,

            task["title"],

            task["priority"]

        )

    await callback.answer(
        "Исполнитель назначен."
    )

    await callback.message.edit_text(

        f"""
✅ Исполнитель назначен

Заявка №{task_id}

👤 {employee['full_name']}

Теперь исполнитель получил уведомление в Telegram.
"""

    )


# ============================================================
# Отмена
# ============================================================

@router.callback_query(lambda c: c.data == "assign_cancel")
async def assign_cancel(callback: CallbackQuery):

    await callback.answer()

    await callback.message.edit_text(

        "Назначение отменено."

    )from aiogram import Router
from aiogram.types import CallbackQuery

from app.services.tasks.service import (
    get_task,
    assign_task
)

from app.services.tasks.history import add_history

from app.services.employee_service import (
    get_team_members,
    get_employee_by_id
)

from app.services.notifications.service import (
    notify_new_task
)

from app.keyboards.tasks.assign import (
    assign_keyboard
)

router = Router()


# ============================================================
# Категория → Команда
# ============================================================

CATEGORY_TEAM = {

    "🚰 Сантехника": "TEAM_TECH",

    "💡 Электрика": "TEAM_TECH",

    "🔧 Техническая": "TEAM_TECH",

    "🧹 Клининг": "TEAM_CLEANING",

    "🛡 Безопасность": "TEAM_SECURITY",

    "🏢 Административная": "ADMINISTRATION",

    "📦 Другое": "TEAM_TECH",

}


# ============================================================
# Выбор исполнителя
# ============================================================

@router.callback_query(lambda c: c.data.startswith("assign:"))
async def choose_employee(callback: CallbackQuery):

    task_id = int(
        callback.data.split(":")[1]
    )

    task = await get_task(task_id)

    if not task:

        await callback.answer(
            "Заявка не найдена.",
            show_alert=True
        )

        return

    team = CATEGORY_TEAM.get(
        task["category"],
        "TEAM_TECH"
    )

    employees = await get_team_members(team)

    if not employees:

        await callback.answer(
            "Нет сотрудников этой команды.",
            show_alert=True
        )

        return

    await callback.message.edit_text(

        f"""
👤 Назначение исполнителя

Заявка №{task['id']}

🏷 {task['title']}

Команда:

{team}
""",

        reply_markup=assign_keyboard(
            employees
        )

    )


# ============================================================
# Назначить сотрудника
# ============================================================

@router.callback_query(lambda c: c.data.startswith("assign_employee:"))
async def assign_employee(callback: CallbackQuery):

    employee_id = int(
        callback.data.split(":")[1]
    )

    task_id = int(
        callback.message.text.split("№")[1].split("\n")[0]
    )

    task = await get_task(task_id)

    employee = await get_employee_by_id(
        employee_id
    )

    if not employee:

        await callback.answer(
            "Сотрудник не найден.",
            show_alert=True
        )

        return

    await assign_task(

        task_id,

        employee_id

    )

    await add_history(

        task_id=task_id,

        employee_id=callback.from_user.id,

        action="ASSIGN",

        comment=f"Назначен {employee['full_name']}"

    )

    # =====================================================
    # Отправляем уведомление исполнителю
    # =====================================================

    if employee["telegram_id"]:

        await notify_new_task(

            employee["telegram_id"],

            task_id,

            task["title"],

            task["priority"]

        )

    await callback.answer(
        "Исполнитель назначен."
    )

    await callback.message.edit_text(

        f"""
✅ Исполнитель назначен

Заявка №{task_id}

👤 {employee['full_name']}

Теперь исполнитель получил уведомление в Telegram.
"""

    )


# ============================================================
# Отмена
# ============================================================

@router.callback_query(lambda c: c.data == "assign_cancel")
async def assign_cancel(callback: CallbackQuery):

    await callback.answer()

    await callback.message.edit_text(

        "Назначение отменено."

    )
