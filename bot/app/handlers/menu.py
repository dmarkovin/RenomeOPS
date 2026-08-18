from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter

from app.services.employees.service import get_employee, update_employee_role, update_employee_team, get_all_employees, get_employee_by_id
from app.services.tasks.service import (
    count_open_tasks,
    count_tasks_by_status,
    count_checking_tasks,
    get_open_tasks,
    get_tasks_by_status,
    count_team_tasks,
    get_team_tasks
)
from app.services.passes.service import count_passes_by_status
from app.services.reception.delivery_service import get_all_deliveries
from app.services.reception.key_service import get_keys
from app.services.reception.document_service import get_documents
from app.services.patrol.service import get_patrols
from app.services.notification_service import notify_admins
from app.database.models import UserRole, Team
from app.keyboards.main_menu import main_menu_keyboard
from app.keyboards.settings import settings_keyboard
from app.keyboards.employees.roles import role_selection_keyboard
from app.keyboards.employees.teams import team_selection_keyboard
from app.keyboards.tasks import tasks_menu_keyboard
from app.keyboards.passes import pass_main_menu_keyboard
from app.keyboards.reception import reception_menu_keyboard
from app.keyboards.reception_keys import key_main_menu_keyboard
from app.keyboards.reception_documents import doc_main_menu_keyboard
from app.keyboards.services import service_admin_keyboard, service_catalog_keyboard
from app.keyboards.employees.admin import employees_admin_menu
from app.states.employees.role_change import RoleChange
from app.states.employees.team_change import TeamChange
from app.states.feedback import Feedback
from app.services.settings.service import get_user_settings, update_setting
from app.services.employees.service import count_employees
from app.services.services.service import get_all_services
from app.keyboards.patrol import patrol_main_menu_keyboard
from sqlalchemy import func, select, and_, cast, String
from app.database import AsyncSessionLocal
from app.database.models import Task

router = Router()

# ========== Функция для главного меню ==========
async def show_main_menu(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    await message.answer("Главное меню:", reply_markup=main_menu_keyboard(employee.role))

# ========== Профиль ==========
@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    text = (
        f"👤 **Ваш профиль**\n\n"
        f"ФИО: {employee.full_name}\n"
        f"Телефон: {employee.phone or '—'}\n"
        f"Роль: {employee.role.value}\n"
        f"Команда: {employee.team.value if employee.team else '—'}\n"
        f"Активен: {'✅ Да' if employee.active else '❌ Нет'}\n"
        f"Telegram ID: {employee.telegram_id or '—'}\n"
        f"Дата регистрации: {employee.registered_at.strftime('%d.%m.%Y %H:%M') if employee.registered_at else '—'}"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=settings_keyboard(employee.role))

# ========== Настройки ==========
@router.message(F.text == "⚙ Настройки")
async def show_settings(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    await message.answer("⚙ Настройки:", reply_markup=settings_keyboard(employee.role))

# ========== Смена команды ==========
@router.message(F.text == "🔄 Сменить команду")
async def change_team(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=team.value, callback_data=f"emp_set_team:{employee.id}:{team.value}")]
        for team in Team
    ] + [[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]])
    await state.set_state(TeamChange.select_team)
    await message.answer("Выберите новую команду:", reply_markup=kb)

@router.callback_query(StateFilter(TeamChange.select_team), F.data.startswith("emp_set_team:"))
async def set_team(callback: CallbackQuery, state: FSMContext):
    _, user_id_str, team_str = callback.data.split(":")
    user_id = int(user_id_str)
    new_team = Team(team_str)
    employee = await get_employee(callback.from_user.id)
    if not employee or user_id != employee.id:
        await callback.answer("Ошибка", show_alert=True)
        return
    await state.set_state(TeamChange.reason)
    await state.update_data(new_team=new_team)
    await callback.message.edit_text("Введите причину смены команды (обязательно):")
    await callback.answer()

@router.message(StateFilter(TeamChange.reason), F.text)
async def process_team_change_reason(message: Message, state: FSMContext):
    reason = message.text.strip()
    if not reason:
        await message.answer("Причина обязательна. Введите текст:")
        return
    data = await state.get_data()
    new_team = data.get("new_team")
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка")
        await state.clear()
        return
    from app.services.tasks.service import create_task
    task = await create_task(
        title=f"Смена команды: {employee.full_name}",
        description=f"Причина: {reason}\nТекущая команда: {employee.team.value if employee.team else '—'}\nНовая команда: {new_team.value}",
        created_by=employee.id,
        is_role_change=True,
        assigned_team=Team.ADMIN_TEAM
    )
    await notify_admins(
        f"📢 Запрос на смену команды от {employee.full_name} (ID: {employee.id}) на {new_team.value}. Задача #{task.id} создана."
    )
    await message.answer(
        f"✅ Запрос на смену команды отправлен администратору. Задача #{task.id} создана."
    )
    await state.clear()

# ========== Уведомления ==========
class SettingsStates(StatesGroup):
    notification_settings = State()

def notification_keyboard(settings) -> InlineKeyboardMarkup:
    buttons = []
    for setting, label in [
        ("notify_task_assigned", "Назначение задач"),
        ("notify_task_status_changed", "Изменение статуса"),
        ("notify_task_comment", "Комментарии"),
        ("notify_new_task_team", "Новые задачи команды"),
        ("notify_checking", "Проверка задач"),
        ("notify_admin", "Административные"),
    ]:
        status = getattr(settings, setting, True)
        emoji = "✅" if status else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{emoji} {label}",
            callback_data=f"notif_toggle:{setting}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="notif_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(F.text == "🔔 Уведомления")
async def notification_settings(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    settings = await get_user_settings(employee.id)
    if not settings:
        await message.answer("Настройки уведомлений не найдены.")
        return
    await state.set_state(SettingsStates.notification_settings)
    await message.answer(
        "Настройки уведомлений:",
        reply_markup=notification_keyboard(settings)
    )

@router.callback_query(F.data.startswith("notif_toggle:"), StateFilter(SettingsStates.notification_settings))
async def toggle_notification(callback: CallbackQuery, state: FSMContext):
    setting = callback.data.split(":")[1]
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    settings = await get_user_settings(employee.id)
    if not settings:
        await callback.answer("Настройки не найдены", show_alert=True)
        return
    current = getattr(settings, setting, True)
    await update_setting(employee.id, setting, not current)
    await callback.answer("✅ Настройка обновлена")
    # Обновляем клавиатуру в текущем сообщении
    settings = await get_user_settings(employee.id)  # обновляем объект
    if settings:
        await callback.message.edit_reply_markup(reply_markup=notification_keyboard(settings))
    else:
        await callback.message.edit_text("Ошибка загрузки настроек.")

@router.callback_query(F.data == "notif_back", StateFilter(SettingsStates.notification_settings))
async def back_from_notifications(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    employee = await get_employee(callback.from_user.id)
    if employee:
        await callback.message.delete()
        await callback.message.answer("⚙ Настройки:", reply_markup=settings_keyboard(employee.role))
    await callback.answer()

# ========== Обратная связь ==========
@router.message(F.text == "📢 Сообщить о проблеме")
async def start_feedback(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    await state.set_state(Feedback.text)
    await message.answer("Опишите проблему или предложение:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    ))

@router.message(Feedback.text, F.text != "❌ Отмена")
async def process_feedback_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await state.set_state(Feedback.photo)
    await message.answer("🖼 Пришлите фото (опционально) или нажмите **Готово**:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Готово")]],
        resize_keyboard=True
    ))

@router.message(Feedback.photo, F.photo)
async def process_feedback_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Добавлено фото ({len(photos)})")

@router.message(Feedback.photo, F.text == "✅ Готово")
async def finish_feedback(message: Message, state: FSMContext):
    data = await state.get_data()
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка")
        await state.clear()
        return
    from app.services.tasks.service import create_task
    task = await create_task(
        title=f"Обратная связь от {employee.full_name}",
        description=data.get('text', ''),
        created_by=employee.id,
        is_feedback=True,
        photo_ids=data.get('photos', []),
        assigned_team=Team.ADMIN_TEAM
    )
    await notify_admins(f"📢 Новая задача о проблеме от {employee.full_name}:\n{data.get('text')}")
    await message.answer(f"✅ Сообщение отправлено администратору. Задача #{task.id} создана.")
    await state.clear()

@router.message(F.text == "❌ Отмена")
async def cancel_action(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=main_menu_keyboard(employee.role) if employee else None)
    if employee:
        await message.answer("Главное меню:", reply_markup=main_menu_keyboard(employee.role))

# ========== Расширенная статистика ==========
@router.message(F.text == "📊 Статистика")
async def show_detailed_statistics(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR):
        await message.answer("Только для администратора и директора.")
        return

    # === Сбор данных ===
    async with AsyncSessionLocal() as db:
        # Общая статистика по задачам
        total_open = await count_open_tasks()
        total_checking = await count_checking_tasks()
        total_closed = await count_tasks_by_status("closed")
        total_waiting = await count_tasks_by_status("waiting")
        total_in_progress = await count_tasks_by_status("in_progress")
        total_accepted = await count_tasks_by_status("accepted")
        total_created = await count_tasks_by_status("created")

        # Задачи по командам (все статусы, кроме closed)
        team_stats = {}
        for team in Team:
            stmt = select(func.count()).select_from(Task).where(
                and_(
                    cast(Task.assigned_team, String) == team.value,
                    cast(Task.status, String) != "closed"
                )
            )
            count = (await db.execute(stmt)).scalar()
            team_stats[team.value] = count

        # Закрытые задачи по командам
        closed_by_team = {}
        for team in Team:
            stmt = select(func.count()).select_from(Task).where(
                and_(
                    cast(Task.assigned_team, String) == team.value,
                    cast(Task.status, String) == "closed"
                )
            )
            count = (await db.execute(stmt)).scalar()
            closed_by_team[team.value] = count

        # Топ исполнителей (закрытые задачи)
        top_executors = []
        result = await db.execute(
            select(Task.assigned_to, func.count())
            .where(cast(Task.status, String) == "closed")
            .group_by(Task.assigned_to)
            .order_by(func.count().desc())
            .limit(5)
        )
        for user_id, count in result:
            if user_id:
                user = await get_employee_by_id(user_id)
                if user:
                    top_executors.append(f"{user.full_name}: {count}")

        # Среднее время выполнения
        avg_time_result = await db.execute(
            select(func.avg(func.extract('epoch', Task.closed_at - Task.created_at)))
            .where(cast(Task.status, String) == "closed")
        )
        avg_seconds = avg_time_result.scalar()
        if avg_seconds:
            avg_hours = avg_seconds / 3600
            avg_time_str = f"{avg_hours:.1f} ч."
        else:
            avg_time_str = "Нет данных"

    # Статистика по пропускам
    active_passes = await count_passes_by_status("active")
    used_passes = await count_passes_by_status("used")
    expired_passes = await count_passes_by_status("expired")
    completed_passes = await count_passes_by_status("completed")

    # Доставка
    all_deliveries = await get_all_deliveries(limit=10000)
    pending_deliveries = len([d for d in all_deliveries if d.status == "pending"])
    received_deliveries = len([d for d in all_deliveries if d.status == "received"])
    completed_deliveries = len([d for d in all_deliveries if d.status == "completed"])

    # Ключи
    issued_keys = len(await get_keys(status="issued", limit=10000))
    returned_keys = len(await get_keys(status="returned", limit=10000))

    # Документы
    docs = await get_documents(limit=10000)
    doc_types = {}
    for d in docs:
        doc_types[d.doc_type] = doc_types.get(d.doc_type, 0) + 1

    # Обходы
    patrols = await get_patrols(limit=10000)
    active_patrols = len([p for p in patrols if p.status == "active"])
    completed_patrols = len([p for p in patrols if p.status == "completed"])

    # Сотрудники
    total_employees = await count_employees(active=None)
    active_employees = await count_employees(active=True)
    inactive_employees = total_employees - active_employees
    role_counts = {}
    for role in UserRole:
        cnt = await count_employees(role=role)
        role_counts[role.value] = cnt

    # Формируем текст
    text = (
        f"📊 <b>Расширенная статистика системы</b>\n\n"
        f"<b>📋 Заявки</b>\n"
        f"Создано: {total_created}\n"
        f"Принято: {total_accepted}\n"
        f"В работе: {total_in_progress}\n"
        f"На проверке: {total_checking}\n"
        f"Ожидают: {total_waiting}\n"
        f"Закрыто: {total_closed}\n"
        f"Открыто (всего): {total_open}\n"
        f"Среднее время выполнения: {avg_time_str}\n\n"
        f"<b>📋 Задачи по командам (открытые):</b>\n"
        + "\n".join([f"{team}: {count}" for team, count in team_stats.items() if count > 0]) + "\n\n"
        f"<b>📋 Закрыто по командам:</b>\n"
        + "\n".join([f"{team}: {count}" for team, count in closed_by_team.items() if count > 0]) + "\n\n"
        f"<b>🏆 Топ исполнителей:</b>\n"
        + ("\n".join(top_executors) if top_executors else "Нет данных") + "\n\n"
        f"<b>🚗 Пропуска</b>\n"
        f"Активные: {active_passes}\n"
        f"Использованные: {used_passes}\n"
        f"Просроченные: {expired_passes}\n"
        f"Выполненные: {completed_passes}\n\n"
        f"<b>📦 Доставка</b>\n"
        f"Ожидают: {pending_deliveries}\n"
        f"Получены: {received_deliveries}\n"
        f"Завершены: {completed_deliveries}\n\n"
        f"<b>🔑 Ключи</b>\n"
        f"Выданы: {issued_keys}\n"
        f"Возвращены: {returned_keys}\n\n"
        f"<b>📄 Документы</b>\n"
        + "\n".join([f"{doc_type}: {count}" for doc_type, count in doc_types.items()]) + "\n\n"
        f"<b>👥 Сотрудники</b>\n"
        f"Всего: {total_employees}\n"
        f"Активные: {active_employees}\n"
        f"Неактивные: {inactive_employees}\n"
        f"По ролям:\n" + "\n".join([f"{role}: {count}" for role, count in role_counts.items() if count > 0])
    )

    await message.answer(text, parse_mode="HTML")

# ========== ГЛОБАЛЬНЫЙ ОБРАБОТЧИК "⬅️ Назад" ==========
@router.message(F.text == "⬅️ Назад")
async def global_back_handler(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return

    current_state = await state.get_state()
    if current_state:
        if current_state.startswith("TaskCreate:") or current_state.startswith("TaskCommentState:"):
            await state.clear()
            await message.answer("📋 Управление заявками:", reply_markup=tasks_menu_keyboard(employee.role))
            return
        elif current_state.startswith("PassCreate:") or current_state.startswith("PassCommentState:"):
            await state.clear()
            await message.answer("🚗 Меню пропусков:", reply_markup=pass_main_menu_keyboard())
            return
        elif current_state.startswith("DeliveryCreate:") or current_state.startswith("DeliveryCommentState:"):
            await state.clear()
            await message.answer("📦 Меню доставки:", reply_markup=reception_menu_keyboard())
            return
        elif current_state.startswith("KeyCreate:") or current_state.startswith("KeyCommentState:"):
            await state.clear()
            await message.answer("🔑 Меню ключей:", reply_markup=key_main_menu_keyboard())
            return
        elif current_state.startswith("DocumentCreate:"):
            await state.clear()
            await message.answer("📄 Меню документов:", reply_markup=doc_main_menu_keyboard())
            return
        elif current_state.startswith("ServiceOrderState:") or current_state.startswith("ServiceEdit:"):
            await state.clear()
            if employee.role == UserRole.ADMIN:
                await message.answer("💳 Управление услугами:", reply_markup=service_admin_keyboard())
            else:
                await message.answer("💳 Каталог услуг:", reply_markup=service_catalog_keyboard(await get_all_services()))
            return
        elif current_state.startswith("EmployeeSearch:"):
            await state.clear()
            await message.answer("👥 Управление сотрудниками:", reply_markup=employees_admin_menu())
            return
        elif current_state.startswith("PatrolCreate:"):
            await state.clear()
            await message.answer("🚶 Меню обходов:", reply_markup=patrol_main_menu_keyboard())
            return

    await message.answer("Главное меню:", reply_markup=main_menu_keyboard(employee.role))
