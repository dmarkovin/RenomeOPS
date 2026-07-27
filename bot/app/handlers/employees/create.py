from aiogram.types import ReplyKeyboardRemove
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from app.services.employees.service import create_employee, get_employee, get_default_team_for_role
from app.states.employees.create import EmployeeRegistration
from app.keyboards.employees.create import role_keyboard, confirm_keyboard
from app.keyboards.employees.admin import employees_admin_menu
from app.database.models import UserRole
from app.utils.invite import generate_invite_link
from app.services.notification_service import notify_admins

router = Router()

@router.message(F.text == "❌ Отмена")
async def cancel_anywhere(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Создание отменено", reply_markup=employees_admin_menu())

@router.message(F.text == "➕ Новый сотрудник")
async def start_create_employee(message: Message, state: FSMContext):
    admin = await get_employee(message.from_user.id)
    if not admin or admin.role != UserRole.ADMIN:
        await message.answer("У вас нет прав.")
        return
    await state.clear()
    await state.set_state(EmployeeRegistration.full_name)
    await message.answer("Введите ФИО нового сотрудника:", reply_markup=ReplyKeyboardRemove())

@router.message(EmployeeRegistration.full_name)
async def process_full_name(message: Message, state: FSMContext):
    full_name = message.text.strip()
    if len(full_name) < 2:
        await message.answer("ФИО должно быть длиннее 2 символов. Попробуйте снова.")
        return
    await state.update_data(full_name=full_name)
    await state.set_state(EmployeeRegistration.phone)
    await message.answer("Введите номер телефона сотрудника (в свободном формате):", reply_markup=ReplyKeyboardRemove())

@router.message(EmployeeRegistration.phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not phone:
        await message.answer("Номер телефона не может быть пустым.")
        return
    await state.update_data(phone=phone)
    await state.set_state(EmployeeRegistration.role)
    await message.answer("Выберите роль сотрудника:", reply_markup=role_keyboard())

@router.message(EmployeeRegistration.role)
async def process_role(message: Message, state: FSMContext):
    role_map = {
        "👑 ADMIN": UserRole.ADMIN,
        "👨‍💼 DIRECTOR": UserRole.DIRECTOR,
        "🛎 CONCIERGE": UserRole.CONCIERGE,
        "🔧 TECHNICIAN": UserRole.TECHNICIAN,
        "🧹 CLEANER": UserRole.CLEANER,
        "🛡 SECURITY": UserRole.SECURITY,
    }
    if message.text not in role_map:
        await message.answer("Пожалуйста, выберите роль с помощью кнопок.")
        return
    role = role_map[message.text]
    await state.update_data(role=role)
    team = get_default_team_for_role(role)
    await state.update_data(team=team)
    await show_confirmation(message, state)

async def show_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    full_name = data.get("full_name")
    phone = data.get("phone")
    role = data.get("role")
    team = data.get("team")
    text = (
        f"📝 Проверьте данные:\n\n"
        f"👤 ФИО: {full_name}\n"
        f"📞 Телефон: {phone}\n"
        f"🎯 Роль: {role.value if role else '—'}\n"
    )
    if team:
        text += f"👥 Команда: {team.value}\n"
    text += "\nПодтвердите создание сотрудника."
    await state.set_state(EmployeeRegistration.confirm)
    await message.answer(text, reply_markup=confirm_keyboard())

@router.message(EmployeeRegistration.confirm, F.text == "✅ Да, создать")
async def confirm_create_employee(message: Message, state: FSMContext):
    data = await state.get_data()
    full_name = data.get("full_name")
    phone = data.get("phone")
    role = data.get("role")
    team = data.get("team")
    try:
        employee = await create_employee(
            full_name=full_name,
            phone=phone,
            role=role,
            team=team,
        )
        invite_link = generate_invite_link(employee.invite_code)
        await message.answer(
            f"✅ Сотрудник успешно создан!\n\n"
            f"👤 ФИО: {employee.full_name}\n"
            f"📞 Телефон: {employee.phone}\n"
            f"🎯 Роль: {employee.role.value}\n"
            f"👥 Команда: {employee.team.value if employee.team else '—'}\n\n"
            f"🔗 Ссылка для регистрации:\n{invite_link}\n\n"
            f"Отправьте эту ссылку сотруднику.",
            reply_markup=employees_admin_menu()
        )
        await notify_admins(f"Новый сотрудник создан: {employee.full_name} ({employee.role.value})")
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Ошибка при создании сотрудника: {str(e)}")
        await state.clear()
        await message.answer("Попробуйте снова.", reply_markup=employees_admin_menu())

@router.message(EmployeeRegistration.confirm, F.text == "❌ Отмена")
async def cancel_confirm(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Создание отменено", reply_markup=employees_admin_menu())

@router.message(EmployeeRegistration.confirm)
async def invalid_confirmation(message: Message):
    await message.answer("Пожалуйста, используйте кнопки для подтверждения или отмены.")
