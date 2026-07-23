from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext


from app.keyboards.employees import employees_keyboard
from app.keyboards.admin import admin_keyboard
from app.keyboards.roles import roles_keyboard


from app.states.employee import EmployeeRegistration

from app.services.employee_service import create_employee


router = Router()



@router.message(
    F.text == "👥 Сотрудники"
)
async def employees_menu(
    message: Message
):

    await message.answer(
        "👥 Управление сотрудниками",
        reply_markup=employees_keyboard()
    )



@router.message(
    F.text == "⬅️ Назад"
)
async def employees_back(
    message: Message
):

    await message.answer(
        "👑 Главное меню администратора",
        reply_markup=admin_keyboard()
    )



@router.message(
    F.text == "➕ Добавить сотрудника"
)
async def add_employee_start(
    message: Message,
    state: FSMContext
):

    await state.set_state(
        EmployeeRegistration.full_name
    )

    await message.answer(
        "Введите ФИО нового сотрудника:"
    )



@router.message(
    EmployeeRegistration.full_name
)
async def employee_full_name(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        full_name=message.text
    )


    await state.set_state(
        EmployeeRegistration.phone
    )


    await message.answer(
        "Введите номер телефона:"
    )



@router.message(
    EmployeeRegistration.phone
)
async def employee_phone(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        phone=message.text
    )


    await state.set_state(
        EmployeeRegistration.role
    )


    await message.answer(
        "Выберите подразделение:",
        reply_markup=roles_keyboard()
    )



@router.message(
    EmployeeRegistration.role
)
async def employee_department(
    message: Message,
    state: FSMContext
):


    departments = {

        "🏢 Администрация": (
            "DIRECTOR",
            "TEAM_ADMINISTRATION"
        ),


        "🛎 Консьерж Сервис": (
            "CONCIERGE",
            "TEAM_CONCIERGE"
        ),


        "🔧 Технический специалист": (
            "TECH_SPECIALIST",
            "TEAM_TECH"
        ),


        "🧹 Сотрудник клининга": (
            "CLEANING",
            "TEAM_CLEANING"
        ),


        "🛡 Охрана": (
            "SECURITY",
            "TEAM_SECURITY"
        )

    }



    if message.text == "❌ Отмена":

        await state.clear()

        await message.answer(
            "❌ Регистрация отменена",
            reply_markup=admin_keyboard()
        )

        return



    if message.text not in departments:

        await message.answer(
            "Выберите подразделение кнопкой."
        )

        return



    role, team = departments[message.text]


    await state.update_data(

        role=role,

        team=team

    )


    await save_employee(
        message,
        state
    )



async def save_employee(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()



    employee = await create_employee(

        telegram_id=0,

        username=None,

        full_name=data["full_name"],

        phone=data["phone"],

        role=data["role"],

        team=data["team"]

    )



    await message.answer(

        f"""
✅ Новый сотрудник создан


👤 ФИО:
{employee['full_name']}


📞 Телефон:
{employee['phone']}


📌 Роль:
{employee['role']}


🏢 Команда:
{employee['team']}


🟢 Статус:
Активен
""",

        reply_markup=admin_keyboard()

    )


    await state.clear()
