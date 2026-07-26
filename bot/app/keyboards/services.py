from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from app.database.models import Service
from typing import List

def service_catalog_keyboard(services: List[Service]) -> InlineKeyboardMarkup:
    buttons = []
    for svc in services:
        buttons.append([InlineKeyboardButton(
            f"💰 {svc.name} — {svc.price} руб.",
            callback_data=f"service_order:{svc.id}"
        )])
    buttons.append([InlineKeyboardButton("⬅ Назад", callback_data="service_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def service_admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Создать услугу")],
            [KeyboardButton(text="📋 Список услуг")],
            [KeyboardButton(text="📦 Заказы")],
            [KeyboardButton(text="⬅ Назад")]
        ],
        resize_keyboard=True
    )

def service_order_status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("✅ Подтвердить", callback_data=f"order_confirm:{order_id}")],
            [InlineKeyboardButton("❌ Отменить", callback_data=f"order_cancel:{order_id}")],
            [InlineKeyboardButton("⬅ Назад", callback_data="service_back")]
        ]
    )

def service_details_keyboard(service_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("📝 Заказать", callback_data=f"service_order:{service_id}")],
            [InlineKeyboardButton("⬅ Назад", callback_data="service_back")]
        ]
    )
