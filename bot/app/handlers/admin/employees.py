from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext


from app.keyboards.employees import employees_keyboard
from app.keyboards.admin import admin_keyboard
from app.keyboards.roles import roles_keyboard
from app.keyboards.teams import teams_keyboard


from app.states.employee import EmployeeRegistration


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
        "Выберите роль сотрудника:",
        reply_markup=roles_keyboard()
    )



@router.message(
    EmployeeRegistration.role
)
async def employee_role(
    message: Message,
    state: FSMContext
):

    roles = {
        "🛎 Консьерж": "CONCIERGE",
        "👨‍💼 Директор": "DIRECTOR",
        "🔧 Исполнитель": "EXECUTOR"
    }


    if message.text not in roles:

        await message.answer(
            "Выберите роль кнопкой ниже."
        )

        return



    await state.update_data(
        role=roles[message.text]
    )


    await state.set_state(
        EmployeeRegistration.team
    )


    await message.answer(
        "Выберите команду:",
        reply_markup=teams_keyboard()
    )



@router.message(
    EmployeeRegistration.team
)
async def employee_team(
    message: Message,
    state: FSMContext
):

    teams = {
        "🔧 Техника": "TEAM_TECH",
        "🧹 Клининг": "TEAM_CLEANING",
        "🛡 Охрана": "TEAM_SECURITY"
    }


    if message.text not in teams:

        await message.answer(
            "Выберите команду кнопкой."
        )

        return



    data = await state.get_data()


    await message.answer(
        f"""
✅ Сотрудник подготовлен

ФИО:
{data['full_name']}

Телефон:
{data['phone']}

Роль:
{data['role']}

Команда:
{teams[message.text]}
"""
    )


    await state.clear()
