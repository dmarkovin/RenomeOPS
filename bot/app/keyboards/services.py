from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from app.database.models import Service, ServiceOrder
from typing import List

def service_catalog_keyboard(services: List[Service]) -> InlineKeyboardMarkup:
    buttons = []
    for svc in services:
        buttons.append([InlineKeyboardButton(
            text=f"💰 {svc.name} — {svc.price} руб.",
            callback_data=f"service_order:{svc.id}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="service_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def service_admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Создать услугу")],
            [KeyboardButton(text="📋 Список услуг")],
            [KeyboardButton(text="📦 Заказы")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True
    )

def service_order_status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплачен", callback_data=f"order_pay:{order_id}")],
            [InlineKeyboardButton(text="✅ Выполнен", callback_data=f"order_complete:{order_id}")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data=f"order_cancel:{order_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="service_back")]
        ]
    )

def service_details_keyboard(service_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Заказать", callback_data=f"service_order:{service_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="service_back")]
        ]
    )

def service_executor_keyboard(employees: List, teams: List) -> InlineKeyboardMarkup:
    buttons = []
    # Сначала команды
    for team in teams:
        buttons.append([InlineKeyboardButton(
            text=f"👥 Команда {team.value}",
            callback_data=f"service_team:{team.value}"
        )])
    # Затем сотрудники
    for emp in employees:
        buttons.append([InlineKeyboardButton(
            text=f"👤 {emp.full_name} ({emp.role.value})",
            callback_data=f"service_emp:{emp.id}"
        )])
    buttons.append([InlineKeyboardButton(text="⏭ Пропустить", callback_data="service_skip_executor")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="service_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def service_admin_list_keyboard(services: list, page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons = []
    for s in services:
        status = "✅" if s.active else "❌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{s.name} — {s.price} руб. {status}",
                callback_data=f"service_admin_edit:{s.id}"
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"service_admin_delete:{s.id}"
            )
        ])
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"service_admin_page:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"service_admin_page:{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="➕ Создать услугу", callback_data="service_admin_create")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="service_admin_back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def service_admin_edit_keyboard(service_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Название", callback_data=f"service_edit_name:{service_id}")],
        [InlineKeyboardButton(text="✏️ Описание", callback_data=f"service_edit_description:{service_id}")],
        [InlineKeyboardButton(text="✏️ Цена", callback_data=f"service_edit_price:{service_id}")],
        [InlineKeyboardButton(text="✏️ Категория", callback_data=f"service_edit_category:{service_id}")],
        [InlineKeyboardButton(text="🔄 Активность", callback_data=f"service_edit_active:{service_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"service_edit_back:{service_id}")],
    ])
