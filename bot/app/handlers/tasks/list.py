from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.services.employees.service import get_employee
from app.services.tasks.service import (
    get_open_tasks,
    get_tasks_for_employee,
    get_team_tasks,
    get_checking_tasks,
    count_open_tasks,
    count_tasks_for_employee,
    count_team_tasks,
    count_checking_tasks,
    get_tasks_by_status,
    count_tasks_by_status,
    get_paid_closed_tasks,
    count_paid_closed_tasks,
    get_regular_closed_tasks,
    count_regular_closed_tasks,
    take_task,
)
from app.database.models import UserRole, TaskStatus
from app.keyboards.tasks import (
    task_list_keyboard,
    get_task_status_emoji,
    get_priority_emoji,
    tasks_menu_keyboard
)
from app.states.tasks.context import TaskContext
from app.states.tasks.search import TaskSearch

router = Router()

def get_task_list_text(title: str, tasks, page, total_pages, show_assignee=True):
    if not tasks:
        return None
    text = f"{title} (стр. {page}/{total_pages}):\n\n"
    for task in tasks:
        status_emoji = get_task_status_emoji(task.status)
        priority_emoji = get_priority_emoji(task.priority)
        paid_marker = "💰 " if getattr(task, 'is_paid', False) else ""
        line = f"{status_emoji} {priority_emoji} #{task.id} **{paid_marker}{task.title[:30]}**"
        if task.status == TaskStatus.WAITING and task.wait_until:
            line += f" ⏳ до {task.wait_until.strftime('%d.%m %H:%M')}"
        text += line + "\n"
        text += f"   Приоритет: {task.priority} | Создал: {task.creator.full_name if task.creator else '—'}"
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
            if hasattr(target, 'from_user'):
                user_id = target.from_user.id
            elif hasattr(target, 'message') and hasattr(target.message, 'from_user'):
                user_id = target.message.from_user.id
            else:
                user_id = target.from_user.id
        employee = await get_employee(user_id)
        if not employee:
            if hasattr(target, 'answer'):
                await target.answer("Вы не зарегистрированы.", show_alert=True)
            else:
                await target.answer("Вы не зарегистрированы.")
            return
        limit = 10
        offset = (page - 1) * limit
        title = ""
        tasks = []
        total = 0
        show_assignee = True

        if list_type == "open":
            tasks = await get_open_tasks(limit=limit, offset=offset)
            total = await count_open_tasks()
            title = "📋 Все открытые заявки"
        elif list_type == "my":
            tasks = await get_tasks_for_employee(employee.id, limit=limit, offset=offset)
            total = await count_tasks_for_employee(employee.id)
            title = "📋 Мои задачи"
            show_assignee = False
        elif list_type == "team":
            tasks = await get_team_tasks(employee.id, limit=limit, offset=offset)
            total = await count_team_tasks(employee.id)
            title = "📋 Новые задачи"
            show_assignee = False
        elif list_type == "checking":
            if employee.role != UserRole.CONCIERGE:
                if hasattr(target, 'answer'):
                    await target.answer("Только для консьержей.", show_alert=True)
                else:
                    await target.answer("Только для консьержей.")
                return
            tasks = await get_checking_tasks(limit=limit, offset=offset)
            total = await count_checking_tasks()
            title = "📋 Задачи на проверке"
        elif list_type == "archive":
            if employee.role in (UserRole.ADMIN, UserRole.DIRECTOR, UserRole.CONCIERGE):
                tasks = await get_tasks_by_status(TaskStatus.CLOSED, limit=limit, offset=offset)
                total = await count_tasks_by_status(TaskStatus.CLOSED)
                title = "📦 Архив (все закрытые заявки)"
            else:
                tasks = await get_tasks_for_employee(employee.id, status=TaskStatus.CLOSED, limit=limit, offset=offset)
                total = await count_tasks_for_employee(employee.id, status=TaskStatus.CLOSED)
                title = "📦 Архив (мои закрытые заявки)"
                show_assignee = False
        elif list_type == "paid_archive":
            tasks = await get_paid_closed_tasks(limit=limit, offset=offset)
            total = await count_paid_closed_tasks()
            title = "💰 Архив платных заявок"
            show_assignee = False
        elif list_type == "regular_archive":
            tasks = await get_regular_closed_tasks(limit=limit, offset=offset)
            total = await count_regular_closed_tasks()
            title = "📋 Архив обычных заявок"
            show_assignee = False

        total_pages = (total + limit - 1) // limit if total > 0 else 1

        if filter_priority:
            tasks = [t for t in tasks if t.priority == filter_priority]
            total = len(tasks)
        if sort_by == "priority":
            tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
        else:
            tasks = sorted(tasks, key=lambda t: t.created_at, reverse=True)

        start = (page - 1) * limit
        tasks_page = tasks[start:start+limit]

        await state.update_data(list_type=list_type, page=page, sort_by=sort_by, filter_priority=filter_priority)
        await state.set_state(TaskContext.list_type)

        if not tasks_page:
            text = f"{title}\n\nНет записей."
            if hasattr(target, 'message'):
                await target.message.delete()
                await target.message.answer(text)
            else:
                await target.answer(text)
            return

        text = get_task_list_text(title, tasks_page, page, total_pages, show_assignee)
        reply_markup = task_list_keyboard(tasks_page, page, total_pages, list_type, filter_priority)
        if hasattr(target, 'message'):
            await target.message.delete()
            await target.message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await target.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e:
        print(f"ERROR in show_list: {e}")
        if hasattr(target, 'answer'):
            await target.answer(f"❌ Ошибка при загрузке списка: {str(e)}", parse_mode=None)
        else:
            await target.message.answer(f"❌ Ошибка при загрузке списка: {str(e)}")

@router.message(F.text == "📋 Заявки")
async def tasks_menu(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee:
        await message.answer("Вы не зарегистрированы.")
        return
    await state.clear()
    await message.answer("📋 Управление заявками:", reply_markup=tasks_menu_keyboard(employee.role))

@router.message(F.text.startswith("📋 Список заявок"))
async def show_all_open_tasks(message: Message, state: FSMContext):
    await show_list(message, state, "open", user_id=message.from_user.id)

@router.message(F.text.startswith("📋 Мои задачи"))
async def show_my_tasks(message: Message, state: FSMContext):
    await show_list(message, state, "my", user_id=message.from_user.id)

@router.message(F.text.startswith("📋 Новые задачи"))
async def show_team_tasks(message: Message, state: FSMContext):
    await show_list(message, state, "team", user_id=message.from_user.id)

@router.message(F.text.startswith("📋 Ожидают проверки"))
async def show_checking_tasks(message: Message, state: FSMContext):
    await show_list(message, state, "checking", user_id=message.from_user.id)

@router.message(F.text.startswith("📦 Архив"))
async def show_archive(message: Message, state: FSMContext):
    await show_list(message, state, "archive", user_id=message.from_user.id)

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
    total_closed = await count_tasks_by_status(TaskStatus.CLOSED)
    total_waiting = await count_tasks_by_status(TaskStatus.WAITING)
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
    list_type = data.get("list_type", "open")
    page = data.get("page", 1)
    sort_by = data.get("sort_by", "date")
    filter_priority = data.get("filter_priority")
    await show_list(callback, state, list_type, page, sort_by, filter_priority, user_id=callback.from_user.id)

@router.message(F.text == "🔍 Поиск по заявкам")
async def start_search(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.CONCIERGE):
        await message.answer("Только для администратора и консьержа.")
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
        assignee_name = task.assignee.full_name if task.assignee else "не назначен"
        paid_marker = "💰 " if getattr(task, 'is_paid', False) else ""
        text += f"{status_emoji} {priority_emoji} #{task.id} **{paid_marker}{task.title[:30]}**\n"
        text += f"   Исполнитель: {assignee_name}\n\n"
    await message.answer(text, parse_mode="HTML")
    await state.clear()
