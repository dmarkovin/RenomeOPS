from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.states.task import TaskCreate
from app.keyboards.tasks import (
    task_categories,
    priority_keyboard,
    confirmation_keyboard
)

from app.keyboards.director import director_keyboard

from app.services.task_service import create_task

router = Router()


# ===========================
# Начало создания заявки
# ===========================

@router.message(F.text == "➕ Новая заявка")
async def task_start(
    message: Message,
    state: FSMContext
):

    await state.clear()

    await state.set_state(TaskCreate.title)

    await message.answer(
        "Введите название заявки:"
    )


# ===========================
# Название
# ===========================

@router.message(TaskCreate.title)
async def task_title(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        title=message.text
    )

    await state.set_state(
        TaskCreate.description
    )

    await message.answer(
        "Введите описание:"
    )


# ===========================
# Описание
# ===========================

@router.message(TaskCreate.description)
async def task_description(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        description=message.text
    )

    await state.set_state(
        TaskCreate.category
    )

    await message.answer(
        "Выберите категорию:",
        reply_markup=task_categories()
    )


# ===========================
# Категория
# ===========================

@router.message(TaskCreate.category)
async def task_category(
    message: Message,
    state: FSMContext
):

    if message.text == "❌ Отмена":

        await state.clear()

        await message.answer(
            "Создание отменено.",
            reply_markup=director_keyboard()
        )

        return

    await state.update_data(
        category=message.text
    )

    await state.set_state(
        TaskCreate.priority
    )

    await message.answer(
        "Выберите приоритет:",
        reply_markup=priority_keyboard()
    )


# ===========================
# Приоритет
# ===========================

@router.message(TaskCreate.priority)
async def task_priority(
    message: Message,
    state: FSMContext
):

    if message.text == "❌ Отмена":

        await state.clear()

        await message.answer(
            "Создание отменено.",
            reply_markup=director_keyboard()
        )

        return

    priorities = {

        "🟢 Низкий": "LOW",

        "🟡 Обычный": "NORMAL",

        "🟠 Высокий": "HIGH",

        "🔴 Авария": "EMERGENCY"

    }

    await state.update_data(
        priority=priorities.get(
            message.text,
            "NORMAL"
        )
    )

    await state.set_state(
        TaskCreate.object
    )

    await message.answer(
        "Введите название объекта:"
    )


# ===========================
# Объект
# ===========================

@router.message(TaskCreate.object)
async def task_object(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        object_name=message.text
    )

    await state.set_state(
        TaskCreate.location
    )

    await message.answer(
        "Введите место выполнения:"
    )


# ===========================
# Локация
# ===========================

@router.message(TaskCreate.location)
async def task_location(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        location=message.text
    )

    await state.set_state(
        TaskCreate.deadline
    )

    await message.answer(
        "Введите дедлайн (например 25.12.2026 18:00) или '-'"
    )


# ===========================
# Дедлайн
# ===========================

@router.message(TaskCreate.deadline)
async def task_deadline(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        deadline=message.text
    )

    data = await state.get_data()

    text = f"""
Проверьте заявку

Название:
{data["title"]}

Описание:
{data["description"]}

Категория:
{data["category"]}

Приоритет:
{data["priority"]}

Объект:
{data["object_name"]}

Локация:
{data["location"]}

Дедлайн:
{data["deadline"]}
"""

    await state.set_state(
        TaskCreate.confirmation
    )

    await message.answer(
        text,
        reply_markup=confirmation_keyboard()
    )


# ===========================
# Подтверждение
# ===========================

@router.message(TaskCreate.confirmation)
async def task_confirmation(
    message: Message,
    state: FSMContext
):

    if message.text != "✅ Создать заявку":

        await state.clear()

        await message.answer(
            "Создание отменено.",
            reply_markup=director_keyboard()
        )

        return

    data = await state.get_data()

    task = await create_task(

        title=data["title"],

        description=data["description"],

        created_by=message.from_user.id,

        category=data["category"],

        location=data["location"],

        priority=data["priority"]

    )

    await state.clear()

    await message.answer(

        f"""
✅ Заявка создана

ID: {task["id"]}

Название:

{task["title"]}

Статус:

{task["status"]}
""",

        reply_markup=director_keyboard()

    )
