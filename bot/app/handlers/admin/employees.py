from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext


from app.keyboards.employees import employees_keyboard
from app.keyboards.admin import admin_keyboard
from app.keyboards.teams import teams_keyboard


from app.states.employee import EmployeeRegistration


from app.services.employee_service import create_employee


from app.utils.invite import generate_invite_link



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

    await state.clear()


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
        full_name=message.text.strip()
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
        phone=message.text.strip()
    )


    await state.set_state(
        EmployeeRegistration.team
    )


    await message.answer(
        "Выберите подразделение:",
        reply_markup=teams_keyboard()
    )




@router.message(
    EmployeeRegistration.team
)
async def employee_team(
    message: Message,
    state: FSMContext
):


    if message.text == "❌ Отмена":

        await state.clear()

        await message.answer(
            "❌ Регистрация отменена",
            reply_markup=admin_keyboard()
        )

        return



    departments = {

        "🏢 Администрация":
        {
            "role": "DIRECTOR",
            "team": "ADMINISTRATION"
        },


        "🛎 Консьерж Сервис":
        {
            "role": "CONCIERGE",
            "team": "CONCIERGE"
        },


        "🔧 Техника":
        {
            "role": "TECHNICIAN",
            "team": "TEAM_TECH"
        },


        "🧹 Клининг":
        {
            "role": "CLEANING",
            "team": "TEAM_CLEANING"
        },


        "🛡 Охрана":
        {
            "role": "SECURITY",
            "team": "TEAM_SECURITY"
        }

    }




    if message.text not in departments:

        await message.answer(
            "⚠️ Выберите подразделение кнопкой."
        )

        return




    data = await state.get_data()


    department = departments[
        message.text
    ]




    employee = await create_employee(

        telegram_id=None,

        username=None,

        full_name=data["full_name"],

        phone=data["phone"],

        role=department["role"],

        team=department["team"]

    )



    invite_link = generate_invite_link(
        employee["invite_code"]
    )



    await state.clear()



    await message.answer(

        f"""
✅ Сотрудник создан!


👤 ФИО:

{employee['full_name']}


📞 Телефон:

{employee['phone']}


🏢 Подразделение:

{message.text}


🎯 Роль:

{employee['role']}


👥 Команда:

{employee['team']}


📲 Telegram:

Не подключен


🔗 Ссылка приглашения:


{invite_link}


Отправьте эту ссылку сотруднику.
"""

    )


    await message.answer(

        "👥 Меню сотрудников",

        reply_markup=employees_keyboard()

    )
