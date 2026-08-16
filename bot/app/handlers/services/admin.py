from aiogram.types import ReplyKeyboardRemove
from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.state import StateFilter

from app.services.employees.service import get_employee
from app.services.services.service import (
    create_service, get_all_services, get_service,
    update_service, delete_service
)
from app.database.models import UserRole
from app.keyboards.services import (
    service_admin_list_keyboard,
    service_admin_edit_keyboard
)
import logging

logger = logging.getLogger(__name__)
router = Router()

class ServiceEdit(StatesGroup):
    name = State()
    description = State()
    price = State()
    category = State()
    confirm_delete = State()

# ===== Проверка прав =====
async def check_admin(user_id: int) -> bool:
    try:
        employee = await get_employee(user_id)
        if not employee:
            logger.warning(f"check_admin: пользователь {user_id} не найден")
            return False
        # Проверяем роль
        is_admin = employee.role == UserRole.ADMIN
        if not is_admin:
            logger.warning(f"check_admin: пользователь {user_id} имеет роль {employee.role}")
        return is_admin
    except Exception as e:
        logger.error(f"check_admin: ошибка {e}")
        return False

# ===== Главное меню =====
@router.message(F.text == "💳 Управление услугами")
async def service_admin_menu(message: Message, state: FSMContext, page: int = 1):
    if not await check_admin(message.from_user.id):
        await message.answer("У вас нет прав.")
        return
    await state.update_data(service_admin_page=page)
    limit = 10
    offset = (page - 1) * limit
    services = await get_all_services(active_only=False, limit=limit, offset=offset)
    total = len(await get_all_services(active_only=False, limit=10000))
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    if not services:
        await message.answer("Услуг пока нет.", reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅️ Назад")]],
            resize_keyboard=True
        ))
        return
    kb = service_admin_list_keyboard(services, page, total_pages)
    await message.answer("📋 Список услуг (администрирование):", reply_markup=kb)

@router.callback_query(F.data.startswith("service_admin_page:"))
async def service_admin_page(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    page = int(callback.data.split(":")[1])
    await service_admin_menu(callback.message, state, page)
    await callback.answer()

@router.callback_query(F.data == "service_admin_create")
async def service_admin_create(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    await callback.message.delete()
    await state.clear()
    await state.set_state(ServiceEdit.name)
    await callback.message.answer("Введите название услуги:", reply_markup=ReplyKeyboardRemove())
    await callback.answer()

@router.message(ServiceEdit.name)
async def service_edit_name(message: Message, state: FSMContext):
    if not await check_admin(message.from_user.id):
        await message.answer("У вас нет прав.")
        return
    data = await state.get_data()
    service_id = data.get("service_id")
    if service_id:
        await update_service(service_id, name=message.text.strip())
        await message.answer("✅ Название обновлено.")
        await state.clear()
        await service_admin_menu(message, state)
    else:
        await state.update_data(name=message.text.strip())
        await state.set_state(ServiceEdit.description)
        await message.answer("Введите описание услуги (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(ServiceEdit.description)
async def service_edit_description(message: Message, state: FSMContext):
    if not await check_admin(message.from_user.id):
        await message.answer("У вас нет прав.")
        return
    data = await state.get_data()
    service_id = data.get("service_id")
    if service_id:
        await update_service(service_id, description=message.text.strip() if message.text != "-" else "")
        await message.answer("✅ Описание обновлено.")
        await state.clear()
        await service_admin_menu(message, state)
    else:
        await state.update_data(description=message.text.strip() if message.text != "-" else "")
        await state.set_state(ServiceEdit.price)
        await message.answer("Введите стоимость услуги (в рублях):", reply_markup=ReplyKeyboardRemove())

@router.message(ServiceEdit.price)
async def service_edit_price(message: Message, state: FSMContext):
    if not await check_admin(message.from_user.id):
        await message.answer("У вас нет прав.")
        return
    data = await state.get_data()
    service_id = data.get("service_id")
    try:
        price = float(message.text.strip())
        if price < 0:
            raise ValueError
    except Exception:
        await message.answer("❌ Введите корректную цену (положительное число).")
        return
    if service_id:
        await update_service(service_id, price=price)
        await message.answer("✅ Цена обновлена.")
        await state.clear()
        await service_admin_menu(message, state)
    else:
        await state.update_data(price=price)
        await state.set_state(ServiceEdit.category)
        await message.answer("Введите категорию услуги (или '-' для пропуска):", reply_markup=ReplyKeyboardRemove())

@router.message(ServiceEdit.category)
async def service_edit_category(message: Message, state: FSMContext):
    if not await check_admin(message.from_user.id):
        await message.answer("У вас нет прав.")
        return
    data = await state.get_data()
    service_id = data.get("service_id")
    if service_id:
        await update_service(service_id, category=message.text.strip() if message.text != "-" else "")
        await message.answer("✅ Категория обновлена.")
        await state.clear()
        await service_admin_menu(message, state)
    else:
        category = message.text.strip() if message.text != "-" else None
        try:
            service = await create_service(
                name=data.get("name"),
                description=data.get("description"),
                price=data.get("price"),
                category=category
            )
            await message.answer(f"✅ Услуга '{service.name}' создана (ID: {service.id})")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()
        await service_admin_menu(message, state)

@router.callback_query(F.data.startswith("service_admin_edit:"))
async def service_admin_edit_start(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    service_id = int(callback.data.split(":")[1])
    service = await get_service(service_id)
    if not service:
        await callback.answer("Услуга не найдена", show_alert=True)
        return
    text = (
        f"📝 <b>Редактирование услуги #{service.id}</b>\n\n"
        f"Название: {service.name}\n"
        f"Описание: {service.description or '—'}\n"
        f"Цена: {service.price} руб.\n"
        f"Категория: {service.category or '—'}\n"
        f"Активна: {'✅ Да' if service.active else '❌ Нет'}\n\n"
        f"Выберите поле для изменения:"
    )
    await callback.message.edit_text(text, reply_markup=service_admin_edit_keyboard(service_id), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("service_edit_name:"))
async def service_edit_name_start(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    service_id = int(callback.data.split(":")[1])
    await state.update_data(service_id=service_id)
    await state.set_state(ServiceEdit.name)
    await callback.message.delete()
    await callback.message.answer("Введите новое название услуги:")
    await callback.answer()

@router.callback_query(F.data.startswith("service_edit_description:"))
async def service_edit_description_start(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    service_id = int(callback.data.split(":")[1])
    await state.update_data(service_id=service_id)
    await state.set_state(ServiceEdit.description)
    await callback.message.delete()
    await callback.message.answer("Введите новое описание услуги (или '-' для пропуска):")
    await callback.answer()

@router.callback_query(F.data.startswith("service_edit_price:"))
async def service_edit_price_start(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    service_id = int(callback.data.split(":")[1])
    await state.update_data(service_id=service_id)
    await state.set_state(ServiceEdit.price)
    await callback.message.delete()
    await callback.message.answer("Введите новую цену (в рублях):")
    await callback.answer()

@router.callback_query(F.data.startswith("service_edit_category:"))
async def service_edit_category_start(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    service_id = int(callback.data.split(":")[1])
    await state.update_data(service_id=service_id)
    await state.set_state(ServiceEdit.category)
    await callback.message.delete()
    await callback.message.answer("Введите новую категорию (или '-' для пропуска):")
    await callback.answer()

@router.callback_query(F.data.startswith("service_edit_active:"))
async def service_edit_active(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    service_id = int(callback.data.split(":")[1])
    service = await get_service(service_id)
    if not service:
        await callback.answer("Услуга не найдена", show_alert=True)
        return
    await update_service(service_id, active=not service.active)
    await callback.answer(f"✅ Статус изменён на {'активна' if not service.active else 'неактивна'}")
    await service_admin_edit_start(callback, state)

@router.callback_query(F.data.startswith("service_edit_back:"))
async def service_edit_back(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    await callback.message.delete()
    await service_admin_menu(callback.message, state)
    await callback.answer()

@router.callback_query(F.data.startswith("service_admin_delete:"))
async def service_admin_delete(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    service_id = int(callback.data.split(":")[1])
    service = await get_service(service_id)
    if not service:
        await callback.answer("Услуга не найдена", show_alert=True)
        return
    await state.set_state(ServiceEdit.confirm_delete)
    await state.update_data(service_id=service_id)
    await callback.message.edit_text(
        f"⚠️ Вы действительно хотите удалить услугу '{service.name}'?\n"
        f"Это действие нельзя отменить. Все заказы с этой услугой останутся в истории.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, удалить", callback_data="service_admin_delete_confirm")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="service_admin_delete_cancel")]
        ])
    )
    await callback.answer()

@router.callback_query(StateFilter(ServiceEdit.confirm_delete), F.data == "service_admin_delete_confirm")
async def service_admin_delete_confirm(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    data = await state.get_data()
    service_id = data.get("service_id")
    success = await delete_service(service_id)
    if success:
        await callback.answer("✅ Услуга удалена (деактивирована)", show_alert=True)
    else:
        await callback.answer("❌ Ошибка", show_alert=True)
    await state.clear()
    await callback.message.delete()
    await service_admin_menu(callback.message, state)

@router.callback_query(StateFilter(ServiceEdit.confirm_delete), F.data == "service_admin_delete_cancel")
async def service_admin_delete_cancel(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    await state.clear()
    await callback.message.delete()
    await service_admin_menu(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "service_admin_back_to_menu")
async def service_admin_back_to_menu(callback: CallbackQuery):
    if not await check_admin(callback.from_user.id):
        await callback.answer("Нет прав", show_alert=True)
        return
    await callback.message.delete()
    employee = await get_employee(callback.from_user.id)
    if employee and employee.role == UserRole.ADMIN:
        from app.keyboards.admin import admin_keyboard
        await callback.message.answer("👑 Главное меню администратора", reply_markup=admin_keyboard())
    await callback.answer()

@router.message(F.text == "⬅️ Назад")
async def back_from_services(message: Message):
    if not await check_admin(message.from_user.id):
        await message.answer("У вас нет прав.")
        return
    employee = await get_employee(message.from_user.id)
    if employee and employee.role == UserRole.ADMIN:
        from app.keyboards.admin import admin_keyboard
        await message.answer("👑 Главное меню администратора", reply_markup=admin_keyboard())
    else:
        await message.answer("Возврат...")
