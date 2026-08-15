from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext

from app.services.employees.service import get_employee
from app.services.tasks.service import (
    get_open_tasks,
    get_tasks_for_employee,
    get_team_tasks,
    get_checking_tasks,
    get_tasks_by_status,
    count_tasks_by_status,
    get_paid_closed_tasks,
    get_regular_closed_tasks,
    take_task,
    get_all_team_tasks,
)
from app.database.models import UserRole
from app.keyboards.tasks import (
    task_list_keyboard,
    get_task_status_emoji,
    get_priority_emoji,
    get_priority_name,
    tasks_menu_keyboard
)
from app.states.tasks.context import TaskContext
from app.states.tasks.search import TaskSearch

router = Router()

async def safe_delete_message(message):
    try:
        await message.delete()
    except Exception:
        pass

def get_navigation_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Назад")],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )

def get_task_list_text(title: str, tasks, page, total_pages, show_assignee=True):
    if not tasks:
        return None
    text = f"{title} (стр. {page}/{total_pages}):\n\n"
    for task in tasks:
        status_emoji = get_task_status_emoji(task.status)
        priority_emoji = get_priority_emoji(task.priority)
        priority_name = get_priority_name(task.priority)
        paid_marker = "💰 " if getattr(task, 'is_paid', False) else ""
        line = f"{status_emoji} {priority_emoji} #{task.id} **{paid_marker}{task.title[:30]}**"
        if task.status == "waiting" and task.wait_until:
            line += f" ⏳ до {task.wait_until.strftime('%d.%m %H:%M')}"
        text += line + "\n"
        text += f"   Приоритет: {priority_name} | Создал: {task.creator.full_name if task.creator else '—'}"
        if show_assignee:
            assignee_name = task.assignee.full_name if task.assignee else "не назначен"
            text += f" | Исполнитель: {assignee_name}"
        text += "\n\n"
    return text

async def show_list(
    target,
    state: FSMContext,
    list_type: str,
    page: int = 1,
    sort_by: str = "date",
    filter_priority: int = None,
    user_id: int = None
):
    try:
        if user_id is None:
            if isinstance(target, CallbackQuery):
                user_id = target.from_user.id
            elif isinstance(target, Message):
                user_id = target.from_user.id
            else:
                user_id = target.from_user.id

        employee = await get_employee(user_id)
        if not employee:
            if isinstance(target, CallbackQuery):
                await target.answer("Вы не зарегистрированы.", show_alert=True)
            else:
                await target.answer("Вы не зарегистрированы.")
            return

        limit = 10
        title = ""
        tasks = []
        show_assignee = True

        if list_type == "open":
            # Все открытые задачи (для администраторов, консьержей, директоров)
            if employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE, UserRole.DIRECTOR):
                if isinstance(target, CallbackQuery):
                    await target.answer("У вас нет прав на просмотр всех заявок.", show_alert=True)
                else:
                    await target.answer("У вас нет прав на просмотр всех заявок.")
                return
            tasks = await get_open_tasks(limit=1000, offset=0, user_id=employee.id)
            title = "📋 Все открытые заявки"
        elif list_type == "my":
            # Мои задачи (только где пользователь исполнитель, включая проверку)
            tasks = await get_tasks_for_employee(employee.id, limit=1000, offset=0, include_closed=False)
            title = "📋 Мои задачи"
            show_assignee = False
        elif list_type == "team":
            # Все задачи команды (включая взятые другими) – "Все задачи"
            tasks = await get_all_team_tasks(employee.id, limit=1000, offset=0, include_closed=False)
            title = "📋 Все задачи"
            show_assignee = True
        elif list_type == "checking":
            if employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE, UserRole.DIRECTOR):
                if isinstance(target, CallbackQuery):
                    await target.answer("Только для консьержей, админов и директоров.", show_alert=True)
                else:
                    await target.answer("Только для консьержей, админов и директоров.")
                return
            tasks = await get_checking_tasks(limit=1000, offset=0)
            title = "📋 Задачи на проверке"
        elif list_type == "archive_all":
            # Все закрытые задачи для админов/консьержей/директоров
            if employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE, UserRole.DIRECTOR):
                if isinstance(target, CallbackQuery):
                    await target.answer("У вас нет прав на просмотр всех закрытых.", show_alert=True)
                else:
                    await target.answer("У вас нет прав на просмотр всех закрытых.")
                return
            tasks = await get_tasks_by_status("closed", limit=1000, offset=0, user_id=employee.id)
            title = "📦 Архив (все закрытые заявки)"
        elif list_type == "archive_team":
            # Архив задач команды (закрытые задачи команды)
            tasks = await get_all_team_tasks(employee.id, limit=1000, offset=0, include_closed=True)
            title = "📦 Архив задач команды"
            show_assignee = True
        elif list_type == "archive_my":
            # Архив личных задач (закрытые задачи, где исполнитель – пользователь)
            tasks = await get_tasks_for_employee(employee.id, limit=1000, offset=0, include_closed=True)
            title = "📦 Архив личных задач"
            show_assignee = False
        elif list_type == "archive_paid":
            tasks = await get_paid_closed_tasks(limit=1000, offset=0, user_id=employee.id)
            title = "💰 Архив платных заявок"
            show_assignee = False
        elif list_type == "archive_regular":
            tasks = await get_regular_closed_tasks(limit=1000, offset=0, user_id=employee.id)
            title = "📋 Личные задачи"
            show_assignee = False
        elif list_type == "archive_feedback":
            if employee.role != UserRole.ADMIN:
                if isinstance(target, CallbackQuery):
                    await target.answer("Только для администратора.", show_alert=True)
                else:
                    await target.answer("Только для администратора.")
                return
            tasks = await get_tasks_by_status("closed", limit=1000, offset=0, user_id=employee.id)
            tasks = [t for t in tasks if getattr(t, 'is_feedback', False)]
            title = "📢 Обращения (проблемы)"
            show_assignee = False
        else:
            tasks = await get_open_tasks(limit=1000, offset=0, user_id=employee.id)
            title = "📋 Все открытые заявки"

        if filter_priority is not None:
            tasks = [t for t in tasks if t.priority == filter_priority]
        if sort_by == "priority":
            tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
        else:
            tasks = sorted(tasks, key=lambda t: t.created_at, reverse=True)

        total = len(tasks)
        total_pages = (total + limit - 1) // limit if total > 0 else 1
        start = (page - 1) * limit
        tasks_page = tasks[start:start+limit]

        await state.update_data(
            list_type=list_type, page=page, sort_by=sort_by, filter_priority=filter_priority,
            current_list_type=list_type, current_page=page, current_sort=sort_by, current_filter=filter_priority
        )
        await state.set_state(TaskContext.list_type)

        if not tasks_page:
            text = f"{title}\n\nНет записей."
            if isinstance(target, CallbackQuery):
                await target.message.answer(text, reply_markup=get_navigation_keyboard(), parse_mode=None)
            else:
                await target.answer(text, reply_markup=get_navigation_keyboard(), parse_mode=None)
            return

        text = get_task_list_text(title, tasks_page, page, total_pages, show_assignee)
        reply_markup = task_list_keyboard(tasks_page, page, total_pages, list_type, filter_priority)

        if isinstance(target, CallbackQuery):
            await target.message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
            await target.message.answer("Выберите действие:", reply_markup=get_navigation_keyboard())
        else:
            await target.answer(text, reply_markup=reply_markup, parse_mode="HTML")
            await target.answer("Выберите действие:", reply_markup=get_navigation_keyboard())
    except Exception as e:
        print(f"ERROR in show_list: {e}")
        if isinstance(target, CallbackQuery):
            await target.message.answer(f"❌ Ошибка при загрузке списка: {str(e)}", parse_mode=None)
        else:
            await target.answer(f"❌ Ошибка при загрузке списка: {str(e)}", parse_mode=None)

async def show_archive_menu(target, state: FSMContext):
    if isinstance(target, CallbackQuery):
        user_id = target.from_user.id
        message_obj = target.message
    else:
        user_id = target.from_user.id
        message_obj = target

    employee = await get_employee(user_id)
    if not employee:
        if isinstance(target, CallbackQuery):
            await target.answer("Вы не зарегистрированы.", show_alert=True)
        else:
            await target.answer("Вы не зарегистрированы.")
        return

    buttons = []
    # Для администраторов, консьержей, директоров – все закрытые
    if employee.role in (UserRole.ADMIN, UserRole.CONCIERGE, UserRole.DIRECTOR):
        buttons.append([InlineKeyboardButton(text="📋 Все закрытые", callback_data="archive_category:all")])
    # Для всех сотрудников – архив команды
    if employee.team is not None:
        buttons.append([InlineKeyboardButton(text="📦 Архив команды", callback_data="archive_category:team")])
    # Архив личных задач – для всех
    buttons.append([InlineKeyboardButton(text="📋 Мои закрытые", callback_data="archive_category:my")])
    if employee.role == UserRole.ADMIN:
        buttons.append([InlineKeyboardButton(text="💰 Платные услуги", callback_data="archive_category:paid")])
        buttons.append([InlineKeyboardButton(text="📢 Обращения (проблемы)", callback_data="archive_category:feedback")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="tasks_back")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    if isinstance(target, CallbackQuery):
        await message_obj.answer("Выберите категорию архива:", reply_markup=kb)
    else:
        await target.answer("Выберите категорию архива:", reply_markup=kb)

@router.callback_query(F.data.startswith("archive_category:"))
async def archive_category_selected(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split(":")[1]
    list_type_map = {
        "all": "archive_all",
        "team": "archive_team",
        "my": "archive_my",
        "paid": "archive_paid",
        "regular": "archive_regular",
        "feedback": "archive_feedback"
    }
    list_type = list_type_map.get(category, "archive_all")
    await safe_delete_message(callback.message)
    await show_list(callback, state, list_type, user_id=callback.from_user.id)
    await callback.answer()

@router.message(F.text == "📋 Заявки")
async def tasks_menu(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    await state.clear()
    await message.answer("📋 Управление заявками:", reply_markup=tasks_menu_keyboard(employee.role, employee.team))

@router.message(F.text.startswith("📋 Список заявок"))
async def show_all_open_tasks(message: Message, state: FSMContext):
    await show_list(message, state, "open", user_id=message.from_user.id)

@router.message(F.text.startswith("📋 Мои задачи"))
async def show_my_tasks(message: Message, state: FSMContext):
    await show_list(message, state, "my", user_id=message.from_user.id)

@router.message(F.text.startswith("📋 Все задачи"))
async def show_team_tasks(message: Message, state: FSMContext):
    await show_list(message, state, "team", user_id=message.from_user.id)

@router.message(F.text.startswith("📋 Ожидают проверки"))
async def show_checking_tasks(message: Message, state: FSMContext):
    await show_list(message, state, "checking", user_id=message.from_user.id)

@router.message(F.text == "📦 Архив")
async def show_archive(message: Message, state: FSMContext):
    await show_archive_menu(message, state)

@router.message(F.text == "📊 Статистика")
async def show_statistics(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR):
        await message.answer("Только для администратора и директора.")
        return
    from app.services.tasks.service import count_open_tasks, count_tasks_by_status, count_checking_tasks
    from app.services.services.service import get_all_orders
    from app.services.employees.service import count_employees
    total_open = await count_open_tasks()
    total_checking = await count_checking_tasks()
    total_closed = await count_tasks_by_status("closed")
    total_waiting = await count_tasks_by_status("waiting")
    total_employees = await count_employees(active=True)
    orders = await get_all_orders(limit=1000)
    total_orders = len([o for o in orders if o.status == "pending"])
    text = (
        f"📊 **Статистика системы**\n\n"
        f"👥 Активных сотрудников: {total_employees}\n"
        f"📋 Открытых заявок: {total_open}\n"
        f"⏳ Ожидают: {total_waiting}\n"
        f"🔄 На проверке: {total_checking}\n"
        f"✅ Закрыто: {total_closed}\n"
        f"💳 Активных заказов услуг: {total_orders}\n"
    )
    await message.answer(text, parse_mode="HTML")

@router.callback_query(F.data.startswith("task_page:"))
async def paginate_tasks(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split(":")[1])
    data = await state.get_data()
    list_type = data.get("list_type", "open")
    sort_by = data.get("sort_by", "date")
    filter_priority = data.get("filter_priority")
    await show_list(callback, state, list_type, page, sort_by, filter_priority, user_id=callback.from_user.id)
    await callback.answer()

@router.callback_query(F.data.startswith("task_sort:"))
async def change_sort(callback: CallbackQuery, state: FSMContext):
    sort_by = callback.data.split(":")[1]
    data = await state.get_data()
    list_type = data.get("list_type", "open")
    page = data.get("page", 1)
    filter_priority = data.get("filter_priority")
    await state.update_data(sort_by=sort_by)
    await show_list(callback, state, list_type, page, sort_by, filter_priority, user_id=callback.from_user.id)
    await callback.answer()

@router.callback_query(F.data.startswith("task_filter:"))
async def change_filter(callback: CallbackQuery, state: FSMContext):
    filter_val = callback.data.split(":")[1]
    if filter_val == "all":
        filter_priority = None
    else:
        filter_priority = int(filter_val)
    data = await state.get_data()
    list_type = data.get("list_type", "open")
    page = data.get("page", 1)
    sort_by = data.get("sort_by", "date")
    await state.update_data(filter_priority=filter_priority)
    await show_list(callback, state, list_type, page, sort_by, filter_priority, user_id=callback.from_user.id)
    await callback.answer()

@router.callback_query(F.data.startswith("task_take_from_list:"))
async def take_from_list(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    employee = await get_employee(callback.from_user.id)
    if not employee:
        await callback.answer("Ошибка", show_alert=True)
        return
    task = await take_task(task_id, employee.id)
    if not task:
        await callback.answer("Не удалось взять задачу", show_alert=True)
        return
    await callback.answer("✅ Задача взята в работу")
    data = await state.get_data()
    list_type = data.get("list_type", "team")
    page = data.get("page", 1)
    sort_by = data.get("sort_by", "date")
    filter_priority = data.get("filter_priority")
    await show_list(callback, state, list_type, page, sort_by, filter_priority, user_id=callback.from_user.id)

@router.callback_query(F.data == "tasks_back")
async def back_to_list(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    prev_list_type = data.get("prev_list_type")
    if prev_list_type:
        page = data.get("prev_page", 1)
        sort_by = data.get("prev_sort", "date")
        filter_priority = data.get("prev_filter")
        await state.update_data(prev_list_type=None, prev_page=None, prev_sort=None, prev_filter=None)
        await show_list(callback, state, prev_list_type, page, sort_by, filter_priority, user_id=callback.from_user.id)
        return
    list_type = data.get("list_type", "open")
    if list_type.startswith("archive_"):
        await show_archive_menu(callback, state)
    else:
        await state.clear()
        employee = await get_employee(callback.from_user.id)
        if employee:
            await callback.message.delete()
            await callback.message.answer("📋 Управление заявками:", reply_markup=tasks_menu_keyboard(employee.role, employee.team))
        else:
            await callback.answer("Ошибка", show_alert=True)
        await callback.answer()

@router.callback_query(F.data == "tasks_back_to_menu")
async def back_to_tasks_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    employee = await get_employee(callback.from_user.id)
    if employee:
        await callback.message.answer("📋 Управление заявками:", reply_markup=tasks_menu_keyboard(employee.role, employee.team))
    await callback.answer()

@router.message(F.text == "⬅️ Назад")
async def back_to_tasks_menu_message(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    await state.clear()
    await message.answer("📋 Управление заявками:", reply_markup=tasks_menu_keyboard(employee.role, employee.team))

@router.message(F.text == "🏠 Главное меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    from app.keyboards.main_menu import main_menu_keyboard
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu_keyboard(employee.role))

@router.message(F.text == "🔍 Поиск по заявкам")
async def start_search(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE, UserRole.DIRECTOR):
        await message.answer("Только для администратора, консьержа и директора.")
        return
    await state.set_state(TaskSearch.query)
    await message.answer("Введите текст для поиска (ID, название, исполнитель):")

@router.message(TaskSearch.query)
async def process_search(message: Message, state: FSMContext):
    query = message.text.strip()
    if len(query) < 2:
        await message.answer("Введите минимум 2 символа.")
        return
    from app.services.tasks.service import search_tasks
    tasks = await search_tasks(query, limit=20)
    if not tasks:
        await message.answer("Ничего не найдено.")
        await state.clear()
        return
    text = "🔍 Результаты поиска:\n\n"
    for task in tasks:
        status_emoji = get_task_status_emoji(task.status)
        priority_emoji = get_priority_emoji(task.priority)
        priority_name = get_priority_name(task.priority)
        assignee_name = task.assignee.full_name if task.assignee else "не назначен"
        paid_marker = "💰 " if getattr(task, 'is_paid', False) else ""
        text += f"{status_emoji} {priority_emoji} #{task.id} **{paid_marker}{task.title[:30]}**\n"
        text += f"   Приоритет: {priority_name} | Исполнитель: {assignee_name}\n\n"
    await message.answer(text, parse_mode="HTML")
    await state.clear()
