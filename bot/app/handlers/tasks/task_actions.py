from aiogram import Router
from aiogram.types import CallbackQuery

from app.services.tasks.service import (
    get_task,
    assign_task,
    update_status,
    complete_task,
)

from app.services.tasks.history import add_history

router = Router()


# ==========================================
# ВЗЯТЬ ЗАЯВКУ
# ==========================================

@router.callback_query(lambda c: c.data.startswith("take:"))
async def task_take(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    task = await get_task(task_id)

    if not task:
        await callback.answer(
            "Заявка не найдена",
            show_alert=True
        )
        return

    await assign_task(
        task_id,
        callback.from_user.id
    )

    await add_history(
        task_id=task_id,
        employee_id=callback.from_user.id,
        action="TAKE"
    )

    await callback.answer(
        "Заявка принята"
    )

    await callback.message.edit_text(
        f"""
✅ Заявка №{task_id}

Статус:

ASSIGNED

Исполнитель назначен.
"""
    )


# ==========================================
# НАЧАТЬ РАБОТУ
# ==========================================

@router.callback_query(lambda c: c.data.startswith("start:"))
async def task_start(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    await update_status(
        task_id,
        "IN_PROGRESS"
    )

    await add_history(
        task_id=task_id,
        employee_id=callback.from_user.id,
        action="START"
    )

    await callback.answer(
        "Работа началась"
    )

    await callback.message.edit_text(
        f"""
▶ Заявка №{task_id}

Работа началась.
"""
    )


# ==========================================
# ПАУЗА
# ==========================================

@router.callback_query(lambda c: c.data.startswith("pause:"))
async def task_pause(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    await update_status(
        task_id,
        "PAUSED"
    )

    await add_history(
        task_id=task_id,
        employee_id=callback.from_user.id,
        action="PAUSE"
    )

    await callback.answer(
        "Работа поставлена на паузу"
    )

    await callback.message.edit_text(
        f"""
⏸ Заявка №{task_id}

Работа приостановлена.
"""
    )


# ==========================================
# ЗАВЕРШИТЬ
# ==========================================

@router.callback_query(lambda c: c.data.startswith("finish:"))
async def task_finish(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    await complete_task(task_id)

    await add_history(
        task_id=task_id,
        employee_id=callback.from_user.id,
        action="DONE"
    )

    await callback.answer(
        "Работа завершена"
    )

    await callback.message.edit_text(
        f"""
✅ Заявка №{task_id}

Работа завершена.
"""
    )


# ==========================================
# ИСТОРИЯ
# ==========================================

@router.callback_query(lambda c: c.data.startswith("history:"))
async def task_history(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    await callback.answer()

    await callback.message.answer(
        f"""
📜 История заявки №{task_id}

(Следующим этапом сюда будет выводиться журнал действий.)
"""
    )


# ==========================================
# ПЕРЕДАТЬ
# ==========================================

@router.callback_query(lambda c: c.data.startswith("transfer:"))
async def task_transfer(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    await callback.answer()

    await callback.message.answer(
        f"""
↔ Передача заявки №{task_id}

Следующим этапом бот покажет сотрудников вашей команды,
после выбора можно будет написать комментарий.
"""
    )


# ==========================================
# ФОТО
# ==========================================

@router.callback_query(lambda c: c.data.startswith("photo:"))
async def task_photo(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    await callback.answer()

    await callback.message.answer(
        f"""
📷 Заявка №{task_id}

Пришлите фотографии.

Будет сохранён только Telegram file_id.
"""
    )


# ==========================================
# НАЗНАЧИТЬ
# ==========================================

@router.callback_query(lambda c: c.data.startswith("assign:"))
async def task_assign(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    await callback.answer()

    await callback.message.answer(
        f"""
👤 Назначение исполнителя

Для заявки №{task_id}

(Следующим этапом будет список сотрудников.)
"""
    )


# ==========================================
# ПЕРЕНАЗНАЧИТЬ
# ==========================================

@router.callback_query(lambda c: c.data.startswith("reassign:"))
async def task_reassign(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    await callback.answer()

    await callback.message.answer(
        f"""
🔄 Переназначение заявки №{task_id}

(Следующим этапом будет выбор нового исполнителя.)
"""
    )


# ==========================================
# ОТКРЫТЬ ДЛЯ КОМАНДЫ
# ==========================================

@router.callback_query(lambda c: c.data.startswith("open:"))
async def task_open(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    await callback.answer()

    await callback.message.answer(
        f"""
👥 Заявка №{task_id}

Теперь доступна всей команде.
"""
    )


# ==========================================
# ОТМЕНА
# ==========================================

@router.callback_query(lambda c: c.data.startswith("cancel:"))
async def task_cancel(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    await update_status(
        task_id,
        "CANCELLED"
    )

    await add_history(
        task_id=task_id,
        employee_id=callback.from_user.id,
        action="CANCEL"
    )

    await callback.answer(
        "Заявка отменена"
    )

    await callback.message.edit_text(
        f"""
❌ Заявка №{task_id}

Отменена.
"""
    )


# ==========================================
# ОЦЕНКА
# ==========================================

@router.callback_query(lambda c: c.data.startswith("rate:"))
async def task_rate(callback: CallbackQuery):

    task_id = int(callback.data.split(":")[1])

    await callback.answer()

    await callback.message.answer(
        f"""
⭐ Оценка заявки №{task_id}

(Следующим этапом будет выбор оценки 1–5.)
"""
    )
