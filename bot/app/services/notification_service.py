from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.config import settings
from app.services.employees.service import get_all_employees, get_employee, get_employee_by_id
from app.services.settings.service import get_user_settings
from app.database.models import UserRole, Team

bot: Bot = None

def set_bot(bot_instance: Bot):
    global bot
    bot = bot_instance

async def _can_send(telegram_id: int, notification_type: str) -> bool:
    """Проверяет, включены ли уведомления данного типа для пользователя по его telegram_id"""
    try:
        employee = await get_employee(telegram_id)
        if not employee:
            return False
        settings = await get_user_settings(employee.id)
        if not settings:
            return True  # если настроек нет, отправляем (по умолчанию включено)
        return getattr(settings, notification_type, True)
    except Exception as e:
        print(f"Ошибка в _can_send: {e}")
        return True

async def notify_admins(text: str, notification_type: str = "notify_admin"):
    if not bot:
        return
    admins = await get_all_employees(role=UserRole.ADMIN)
    for admin in admins:
        if admin.telegram_id and await _can_send(admin.telegram_id, notification_type):
            try:
                await bot.send_message(admin.telegram_id, text)
            except Exception as e:
                print(f"Ошибка отправки админу {admin.telegram_id}: {e}")

async def notify_user(telegram_id: int, text: str, notification_type: str = "notify_task_assigned"):
    if not bot:
        return
    if await _can_send(telegram_id, notification_type):
        try:
            await bot.send_message(telegram_id, text)
        except Exception as e:
            print(f"Ошибка отправки пользователю {telegram_id}: {e}")

async def notify_team(team: Team, text: str, notification_type: str = "notify_new_task_team"):
    if not bot:
        return
    employees = await get_all_employees(team=team, active=True)
    for emp in employees:
        if emp.telegram_id and await _can_send(emp.telegram_id, notification_type):
            try:
                await bot.send_message(emp.telegram_id, text)
            except Exception as e:
                print(f"Ошибка отправки члену команды {emp.telegram_id}: {e}")

async def notify_team_with_button(team: Team, text: str, task_id: int, notification_type: str = "notify_new_task_team"):
    if not bot:
        return
    employees = await get_all_employees(team=team, active=True)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📥 Взять в работу", callback_data=f"task_take_from_list:{task_id}")]
        ]
    )
    for emp in employees:
        if emp.telegram_id and await _can_send(emp.telegram_id, notification_type):
            try:
                await bot.send_message(emp.telegram_id, text, reply_markup=keyboard)
            except Exception as e:
                print(f"Ошибка отправки {emp.telegram_id}: {e}")

async def notify_concierges(text: str, notification_type: str = "notify_checking"):
    if not bot:
        return
    employees = await get_all_employees(role=UserRole.CONCIERGE, active=True)
    for emp in employees:
        if emp.telegram_id and await _can_send(emp.telegram_id, notification_type):
            try:
                await bot.send_message(emp.telegram_id, text)
            except Exception as e:
                print(f"Ошибка отправки консьержу {emp.telegram_id}: {e}")

async def notify_security(text: str):
    if not bot:
        return
    employees = await get_all_employees(role=UserRole.SECURITY, active=True)
    for emp in employees:
        if emp.telegram_id:
            try:
                await bot.send_message(emp.telegram_id, text)
            except Exception as e:
                print(f"Ошибка отправки охране {emp.telegram_id}: {e}")
