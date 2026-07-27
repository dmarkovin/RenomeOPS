from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from app.database.models import Pass
from typing import List


def pass_list_keyboard(passes: List[Pass], page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons = []
    for p in passes[:10]:
        status_emoji = "🟢" if p.status == "active" else "🔵" if p.status == "used" else "🔴" if p.status == "expired" else "✅" if p.status == "completed" else "⚪"
        label = f"{status_emoji} #{p.id} "
        if p.type == "guest":
            label += f"{p.guest_name or 'Гость'}"
        else:
            label += f"{p.car_number or 'Авто'}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"pass:{p.id}")])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"pass_page:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"pass_page:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    buttons.append([InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="pass_menu_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def pass_action_keyboard(pass_id: int, status: str, user_role: str) -> InlineKeyboardMarkup:
    buttons = []
    if status == "active":
        buttons.append([InlineKeyboardButton(text="✅ Въезд", callback_data=f"pass_checkin:{pass_id}")])
    elif status == "used":
        buttons.append([InlineKeyboardButton(text="🚗 Выезд", callback_data=f"pass_checkout:{pass_id}")])
    if user_role in ("CONCIERGE", "ADMIN", "DIRECTOR"):
        if status not in ("completed", "expired"):
            buttons.append([InlineKeyboardButton(text="✅ Выполнено", callback_data=f"pass_complete:{pass_id}")])
    if status not in ("expired", "completed"):
        buttons.append([InlineKeyboardButton(text="🔒 Закрыть", callback_data=f"pass_close:{pass_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="pass_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def pass_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Заказать пропуск")],
            [KeyboardButton(text="📋 Активные пропуски")],
            [KeyboardButton(text="📜 История пропусков")],
            [KeyboardButton(text="🔍 Поиск по пропускам")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )

def pass_assign_type_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора типа назначения для пропуска"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Всей охране")],
            [KeyboardButton(text="👤 Конкретному сотруднику")],
            [KeyboardButton(text="⏭ Пропустить")],
        ],
        resize_keyboard=True
    )
