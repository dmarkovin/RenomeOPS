from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.config import settings
from app.services.employees.service import get_all_employees, get_employee, get_employee_by_id
from app.services.settings.service import get_user_settings
from app.database.models import UserRole, Team
import asyncio
import logging
import time

bot: Bot = None
_settings_cache = {}
CACHE_TTL = 300  # 5 минут

def set_bot(bot_instance: Bot):
    global bot
    bot = bot_instance

async def _can_send(telegram_id: int, notification_type: str) -> bool:
    try:
        cache_key = f"{telegram_id}:{notification_type}"
        now = time.time()
        if cache_key in _settings_cache:
            value, cached_at = _settings_cache[cache_key]
            if now - cached_at < CACHE_TTL:
                return value
            else:
                del _settings_cache[cache_key]

        employee = await get_employee(telegram_id)
        if not employee:
            _settings_cache[cache_key] = (False, now)
            return False
        settings = await get_user_settings(employee.id)
        if not settings:
            _settings_cache[cache_key] = (True, now)
            return True
        result = getattr(settings, notification_type, True)
        _settings_cache[cache_key] = (result, now)
        return result
    except Exception as e:
        logging.error(f"Ошибка в _can_send для telegram_id {telegram_id}: {e}")
        return True

async def _send_message(telegram_id: int, text: str, reply_markup=None, retries: int = 3):
    if not bot:
        logging.error("Bot не инициализирован, уведомление не отправлено")
        return
    for attempt in range(retries):
        try:
            await bot.send_message(telegram_id, text, reply_markup=reply_markup)
            return
        except Exception as e:
            logging.warning(f"Ошибка отправки (попытка {attempt+1}/{retries}) для {telegram_id}: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(1)
    logging.error(f"Не удалось отправить сообщение пользователю {telegram_id} после {retries} попыток")

def task_view_button(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Посмотреть заявку", callback_data=f"task:{task_id}")]
        ]
    )

async def notify_admins(text: str, notification_type: str = "notify_admin"):
    if not bot:
        return
    admins = await get_all_employees(role=UserRole.ADMIN)
    for admin in admins:
        if admin.telegram_id and await _can_send(admin.telegram_id, notification_type):
            await _send_message(admin.telegram_id, text)

async def notify_user(telegram_id: int, text: str, notification_type: str = "notify_task_assigned", task_id: int = None):
    if not bot or not telegram_id:
        return
    if await _can_send(telegram_id, notification_type):
        kb = task_view_button(task_id) if task_id else None
        await _send_message(telegram_id, text, kb)

async def notify_user_with_button(telegram_id: int, text: str, task_id: int, notification_type: str = "notify_task_assigned"):
    """Отправляет уведомление пользователю с кнопкой 'Посмотреть заявку'"""
    if not bot or not telegram_id:
        return
    if await _can_send(telegram_id, notification_type):
        kb = task_view_button(task_id)
        await _send_message(telegram_id, text, kb)

async def notify_team(team: Team, text: str, notification_type: str = "notify_new_task_team", task_id: int = None):
    if not bot:
        return
    employees = await get_all_employees(team=team, active=True)
    for emp in employees:
        if emp.telegram_id and await _can_send(emp.telegram_id, notification_type):
            kb = task_view_button(task_id) if task_id else None
            await _send_message(emp.telegram_id, text, kb)

async def notify_team_with_button(team: Team, text: str, task_id: int, notification_type: str = "notify_new_task_team"):
    if not bot:
        return
    employees = await get_all_employees(team=team, active=True)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📥 Взять в работу", callback_data=f"task_take_from_list:{task_id}")],
            [InlineKeyboardButton(text="📋 Посмотреть заявку", callback_data=f"task:{task_id}")]
        ]
    )
    for emp in employees:
        if emp.telegram_id and await _can_send(emp.telegram_id, notification_type):
            await _send_message(emp.telegram_id, text, keyboard)

async def notify_concierges(text: str, notification_type: str = "notify_checking", task_id: int = None):
    if not bot:
        return
    employees = await get_all_employees(role=UserRole.CONCIERGE, active=True)
    for emp in employees:
        if emp.telegram_id and await _can_send(emp.telegram_id, notification_type):
            kb = task_view_button(task_id) if task_id else None
            await _send_message(emp.telegram_id, text, kb)

async def notify_security(text: str, notification_type: str = "notify_security"):
    if not bot:
        return
    employees = await get_all_employees(role=UserRole.SECURITY, active=True)
    for emp in employees:
        if emp.telegram_id:
            await _send_message(emp.telegram_id, text)
