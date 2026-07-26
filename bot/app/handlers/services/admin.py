from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.services.employees.service import get_employee
from app.services.services.service import create_service, get_all_services, get_all_orders, update_order_status
from app.database.models import UserRole
from app.keyboards.services import service_admin_keyboard

router = Router()

class ServiceCreation(StatesGroup):
    name = State()
    description = State()
    price = State()
    category = State()
    confirm = State()

@router.message(F.text == "➕ Создать услугу")
async def start_create_service(message: Message, state: FSMContext):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR):
        await message.answer("У вас нет прав.")
        return
    await state.clear()
    await state.set_state(ServiceCreation.name)
    await message.answer("Введите название услуги:")

@router.message(ServiceCreation.name)
async def service_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(ServiceCreation.description)
    await message.answer("Введите описание услуги (или '-' для пропуска):")

@router.message(ServiceCreation.description)
async def service_description(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(description=text if text != "-" else None)
    await state.set_state(ServiceCreation.price)
    await message.answer("Введите стоимость услуги (в рублях):")

@router.message(ServiceCreation.price)
async def service_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.strip())
        if price < 0:
            raise ValueError
    except:
        await message.answer("Введите корректную цену (положительное число).")
        return
    await state.update_data(price=price)
    await state.set_state(ServiceCreation.category)
    await message.answer("Введите категорию услуги (или '-' для пропуска):")

@router.message(ServiceCreation.category)
async def service_category(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(category=text if text != "-" else None)
    data = await state.get_data()
    await state.set_state(ServiceCreation.confirm)
    text = (
        f"📝 Проверьте данные:\n"
        f"Название: {data['name']}\n"
        f"Описание: {data['description'] or '—'}\n"
        f"Цена: {data['price']} руб.\n"
        f"Категория: {data['category'] or '—'}\n\n"
        f"Подтвердить создание? (да/нет)"
    )
    await message.answer(text)

@router.message(ServiceCreation.confirm, F.text.lower() == "да")
async def confirm_create_service(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        service = await create_service(
            name=data['name'],
            description=data.get('description'),
            price=data['price'],
            category=data.get('category')
        )
        await message.answer(f"✅ Услуга '{service.name}' создана (ID: {service.id})", reply_markup=service_admin_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    await state.clear()

@router.message(ServiceCreation.confirm, F.text.lower() == "нет")
async def cancel_create_service(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Создание отменено", reply_markup=service_admin_keyboard())

@router.message(ServiceCreation.confirm)
async def invalid_confirm(message: Message):
    await message.answer("Ответьте 'да' или 'нет'")

@router.message(F.text == "📋 Список услуг")
async def list_services(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR):
        await message.answer("Нет прав.")
        return
    services = await get_all_services(active_only=False)
    if not services:
        await message.answer("Услуг пока нет.")
        return
    text = "📋 Список услуг:\n\n"
    for s in services:
        status = "✅" if s.active else "❌"
        text += f"{status} {s.name} — {s.price} руб. (ID: {s.id})\n"
    await message.answer(text, reply_markup=service_admin_keyboard())

@router.message(F.text == "📦 Заказы")
async def list_orders(message: Message):
    employee = await get_employee(message.from_user.id)
    if not employee or employee.role not in (UserRole.ADMIN, UserRole.DIRECTOR):
        await message.answer("Нет прав.")
        return
    orders = await get_all_orders(limit=20)
    if not orders:
        await message.answer("Заказов пока нет.")
        return
    text = "📦 Заказы услуг:\n\n"
    for o in orders:
        text += f"ID: {o.id} | Услуга ID: {o.service_id} | Статус: {o.status} | Создан: {o.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    await message.answer(text, reply_markup=service_admin_keyboard())
