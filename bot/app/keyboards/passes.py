from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from app.database.models import Pass
from typing import List


def pass_list_keyboard(passes: List[Pass], page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons = []
    for p in passes[:10]:
        if p.status == "active":
            status_emoji = "🟢"
        elif p.status == "used":
            status_emoji = "🔵"
        elif p.status == "expired":
            status_emoji = "❗"
        elif p.status == "completed":
            status_emoji = "✅"
        else:
            status_emoji = "⚪"

        if p.type == "guest":
            type_icon = "👤"
            name = p.guest_name or "Гость"
        else:
            type_icon = "🚗"
            name = p.car_number or "Авто"

        label = f"{status_emoji} {type_icon} #{p.id} {name}"
        if p.apartment:
            label += f" | кв.{p.apartment}"
        if p.purpose:
            label += f" | {p.purpose[:20]}"
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


def pass_action_keyboard(pass_id: int, status: str, user_role: str, checked_in: bool = False, checked_out: bool = False) -> InlineKeyboardMarkup:
    buttons = []
    # Кнопка въезда/выезда/выполнено
    if status == "active":
        if not checked_in:
            buttons.append([InlineKeyboardButton(text="✅ Въезд", callback_data=f"pass_checkin:{pass_id}")])
        elif not checked_out:
            buttons.append([InlineKeyboardButton(text="🚗 Выезд", callback_data=f"pass_checkout:{pass_id}")])
        else:
            if user_role in ("CONCIERGE", "ADMIN", "DIRECTOR", "SECURITY"):
                buttons.append([InlineKeyboardButton(text="✅ Выполнено", callback_data=f"pass_complete:{pass_id}")])
    elif status == "used":
        if not checked_out:
            buttons.append([InlineKeyboardButton(text="🚗 Выезд", callback_data=f"pass_checkout:{pass_id}")])
        else:
            if user_role in ("CONCIERGE", "ADMIN", "DIRECTOR", "SECURITY"):
                buttons.append([InlineKeyboardButton(text="✅ Выполнено", callback_data=f"pass_complete:{pass_id}")])
    elif status == "completed":
        pass

    # Кнопка "Закрыть" для ролей с правом
    if status not in ("completed", "expired") and user_role in ("CONCIERGE", "ADMIN", "DIRECTOR"):
        buttons.append([InlineKeyboardButton(text="🔒 Закрыть", callback_data=f"pass_close:{pass_id}")])

    # Комментарии и история
    buttons.append([
        InlineKeyboardButton(text="💬 Комментарии", callback_data=f"pass_comment_menu:{pass_id}"),
        InlineKeyboardButton(text="📜 История", callback_data=f"pass_history:{pass_id}"),
    ])
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
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Всей охране")],
            [KeyboardButton(text="👤 Конкретному сотруднику")],
            [KeyboardButton(text="⏭ Пропустить")],
        ],
        resize_keyboard=True
    )
