from aiogram import Bot
from app.config import settings
from app.services.employees.service import get_all_employees
from app.database.models import UserRole, Team

bot: Bot = None

def set_bot(bot_instance: Bot):
    global bot
    bot = bot_instance

async def notify_admin(text: str):
    """Отправить уведомление всем администраторам (устаревшая функция, используйте notify_admins)"""
    await notify_admins(text)

async def notify_admins(text: str):
    if not bot:
        return
    admins = await get_all_employees(role=UserRole.ADMIN)
    for admin in admins:
        if admin.telegram_id:
            try:
                await bot.send_message(admin.telegram_id, text)
            except Exception as e:
                print(f"Ошибка отправки админу {admin.telegram_id}: {e}")

async def notify_user(user_id: int, text: str):
    if not bot:
        return
    try:
        await bot.send_message(user_id, text)
    except Exception as e:
        print(f"Ошибка отправки пользователю {user_id}: {e}")

async def notify_team(team: Team, text: str):
    if not bot:
        return
    employees = await get_all_employees(team=team, active=True)
    for emp in employees:
        if emp.telegram_id:
            await notify_user(emp.telegram_id, text)
