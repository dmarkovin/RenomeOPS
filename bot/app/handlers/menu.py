from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter

from app.services.employees.service import get_employee
from app.services.notification_service import notify_admins
from app.database.models import UserRole, Team
from app.keyboards.main_menu import main_menu_keyboard
from app.keyboards.settings import settings_keyboard
from app.keyboards.employees.roles import role_selection_keyboard
from app.services.employees.service import update_employee_role
from app.services.settings.service import get_user_settings, update_setting
from app.keyboards.notification_settings import notification_settings_keyboard
from app.states.feedback import Feedback
from app.services.tasks.service import create_task
from app.services.employees.service import get_all_employees
from app.states.employees.team_change import TeamChange
from app.keyboards.employees.teams import team_selection_keyboard

router = Router()

class SettingsStates(StatesGroup):
    change_role = State()
    notification_settings = State()

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
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "⚙ Настройки")
async def settings_menu(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    await message.answer("⚙ Настройки:", reply_markup=settings_keyboard(employee.role))

# ===== Смена роли для администратора (мгновенно) =====
@router.message(F.text == "🔄 Сменить роль")
async def change_own_role(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role != UserRole.ADMIN:
        await message.answer("Только для администратора.")
        return
    await state.set_state(SettingsStates.change_role)
    await state.update_data(user_id=employee.id)
    await message.answer(
        "⚠️ Внимание! Если вы измените свою роль, вы можете потерять доступ к административным функциям.\n"
        "Чтобы восстановить роль, используйте команду /become_admin.\n\n"
        "Выберите новую роль:",
        reply_markup=role_selection_keyboard(employee.id)
    )

@router.callback_query(F.data.startswith("emp_set_role:"), StateFilter(SettingsStates.change_role))
async def set_own_role(callback: CallbackQuery, state: FSMContext):
    _, user_id_str, role_str = callback.data.split(":")
    user_id = int(user_id_str)
    new_role = UserRole(role_str)
    user = await update_employee_role(user_id, new_role)
    if user:
        await callback.answer(f"✅ Ваша роль изменена на {new_role.value}", show_alert=True)
        await state.clear()
        employee = await get_employee(callback.from_user.id)
        if employee:
            await callback.message.edit_text("⚙ Настройки:", reply_markup=settings_keyboard(new_role))
    else:
        await callback.answer("Ошибка", show_alert=True)

# ===== Смена команды (для всех, кроме ADMIN) =====
@router.message(F.text == "🔄 Сменить команду")
async def change_team_start(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    if employee.role == UserRole.ADMIN:
        await message.answer("Администратор может сменить команду через карточку сотрудника.")
        return
    await state.set_state(TeamChange.select_team)
    await message.answer("Выберите новую команду:", reply_markup=team_selection_keyboard(employee.id))

@router.callback_query(StateFilter(TeamChange.select_team), F.data.startswith("emp_set_team:"))
async def team_selected(callback: CallbackQuery, state: FSMContext):
    _, user_id_str, team_str = callback.data.split(":")
    user_id = int(user_id_str)
    new_team = Team(team_str) if team_str != "None" else None
    await state.update_data(new_team=new_team, user_id=user_id)
    await state.set_state(TeamChange.reason)
    await callback.message.edit_text("Напишите обоснование для смены команды:")

@router.message(StateFilter(TeamChange.reason), F.text)
async def process_team_change_reason(message: Message, state: FSMContext):
    reason = message.text
    data = await state.get_data()
    user_id = data.get("user_id")
    new_team = data.get("new_team")
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка")
        await state.clear()
        return

    task = await create_task(
        title=f"Запрос на смену команды для {employee.full_name}",
        description=f"Пользователь {employee.full_name} (ID: {employee.id}) запрашивает смену команды на {new_team.value if new_team else 'без команды'}.\nОбоснование: {reason}",
        created_by=employee.id,
        priority=3,
        is_feedback=True,
        is_role_change=True,
        assigned_team=Team.ADMIN_TEAM
    )
    from app.services.tasks.service import assign_task_to_user
    admins = await get_all_employees(role=UserRole.ADMIN, active=True)
    if admins:
        await assign_task_to_user(task.id, admins[0].id, employee.id)
        await notify_admins(f"📢 Запрос на смену команды от {employee.full_name} (ID: {employee.id}) на {new_team.value if new_team else 'без команды'}. Задача #{task.id} создана.")
        await message.answer(f"✅ Запрос на смену команды отправлен администраторам. Задача #{task.id} создана.")
    else:
        await message.answer("⚠️ Нет доступных администраторов. Запрос создан, но не назначен.")
    await state.clear()

@router.message(F.text == "🔔 Уведомления")
async def open_notification_settings(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    settings = await get_user_settings(employee.id)
    await state.set_state(SettingsStates.notification_settings)
    await message.answer(
        "🔔 **Настройки уведомлений**\n\n"
        "Здесь вы можете включить или отключить отдельные типы уведомлений.\n"
        "✅ – включено, ❌ – отключено.",
        reply_markup=notification_settings_keyboard(settings),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("notif_toggle:"), StateFilter(SettingsStates.notification_settings))
async def toggle_notification(callback: CallbackQuery, state: FSMContext):
    setting_name = callback.data.split(":")[1]
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    settings = await get_user_settings(employee.id)
    current_value = getattr(settings, setting_name)
    new_value = not current_value
    await update_setting(employee.id, setting_name, new_value)
    settings = await get_user_settings(employee.id)
    await callback.message.edit_text(
        "🔔 **Настройки уведомлений**\n\n"
        "Здесь вы можете включить или отключить отдельные типы уведомлений.\n"
        "✅ – включено, ❌ – отключено.",
        reply_markup=notification_settings_keyboard(settings),
        parse_mode="HTML"
    )
    await callback.answer("Настройка сохранена")

@router.callback_query(F.data == "notif_back", StateFilter(SettingsStates.notification_settings))
async def back_from_notifications(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.message.delete()
        await callback.answer()
        return
    await callback.message.delete()
    await callback.message.answer("⚙ Настройки:", reply_markup=settings_keyboard(employee.role))
    await callback.answer()

@router.message(F.text == "⬅️ Назад")
async def back_from_settings(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Возврат...")
        return
    await message.answer("Главное меню:", reply_markup=main_menu_keyboard(employee.role))

# ========== Сообщить о проблеме ==========
@router.message(F.text == "📢 Сообщить о проблеме")
async def start_feedback(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    await state.set_state(Feedback.text)
    await message.answer("Опишите проблему, с которой вы столкнулись:", reply_markup=ReplyKeyboardRemove())

@router.message(Feedback.text)
async def process_feedback_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await state.set_state(Feedback.photo)
    await message.answer(
        "Пришлите скриншот (опционально) или нажмите **Готово**:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="✅ Готово")]],
            resize_keyboard=True
        )
    )

@router.message(Feedback.photo, F.photo)
async def process_feedback_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Фото добавлено ({len(photos)})")

@router.message(Feedback.photo, F.text == "✅ Готово")
async def finish_feedback(message: Message, state: FSMContext):
    data = await state.get_data()
    text = data.get("text")
    photos = data.get("photos", [])
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Ошибка")
        await state.clear()
        return

    task = await create_task(
        title=f"Проблема от {employee.full_name}",
        description=text,
        created_by=employee.id,
        priority=5,
        photo_ids=photos,
        is_paid=False,
        is_feedback=True
    )

    admins = await get_all_employees(role=UserRole.ADMIN, active=True)
    if admins:
        from app.services.tasks.service import assign_task_to_user
        admin = admins[0]
        await assign_task_to_user(task.id, admin.id, employee.id)
        await notify_admins(f"📢 Создана задача о проблеме от {employee.full_name}:\n{text}")
    else:
        concierges = await get_all_employees(role=UserRole.CONCIERGE, active=True)
        if concierges:
            from app.services.tasks.service import assign_task_to_user
            await assign_task_to_user(task.id, concierges[0].id, employee.id)
            await notify_admins(f"📢 Создана задача о проблеме от {employee.full_name} (назначена консьержу):\n{text}")
        else:
            await message.answer("⚠️ Нет доступных администраторов или консьержей. Задача создана, но не назначена.")

    await message.answer(f"✅ Ваше сообщение зарегистрировано как заявка #{task.id}. Администратор получил уведомление.")
    await state.clear()
    await message.answer("Возврат в главное меню", reply_markup=main_menu_keyboard(employee.role))

async def show_main_menu(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    await message.answer("Главное меню:", reply_markup=main_menu_keyboard(employee.role))
