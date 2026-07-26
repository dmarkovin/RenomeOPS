from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext


from app.states.employees.create import EmployeeCreateState

from app.keyboards.employees.create import (
    employee_roles_keyboard
)

from app.keyboards.teams import teams_keyboard

from app.services.employees.service import (
    create_employee
)

from app.database.models import (
    UserRole,
    Team
)


router = Router()



@router.message(
    F.text == "👤 Новый сотрудник"
)
async def create_start(
    message: Message,
    state: FSMContext
):

    await state.set_state(
        EmployeeCreateState.full_name
    )

    await message.answer(
        "Введите ФИО сотрудника:"
    )



@router.message(
    EmployeeCreateState.full_name
)
async def get_name(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        full_name=message.text
    )


    await state.set_state(
        EmployeeCreateState.phone
    )


    await message.answer(
        "Введите телефон:"
    )



@router.message(
    EmployeeCreateState.phone
)
async def get_phone(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        phone=message.text
    )


    await state.set_state(
        EmployeeCreateState.role
    )


    await message.answer(
        "Выберите роль:",
        reply_markup=employee_roles_keyboard()
    )



@router.message(
    EmployeeCreateState.role
)
async def get_role(
    message: Message,
    state: FSMContext
):

    roles = {

        "🛎 Консьерж":
            UserRole.CONCIERGE,

        "🔧 Техник":
            UserRole.TECHNICIAN,

        "🧹 Уборка":
            UserRole.CLEANER,

        "🛡 Охрана":
            UserRole.SECURITY,

        "👨‍💼 Директор":
            UserRole.DIRECTOR,

    }


    role = roles.get(
        message.text
    )


    if not role:

        await message.answer(
            "Выберите роль кнопкой"
        )

        return


    await state.update_data(
        role=role
    )


    if role in [
        UserRole.TECHNICIAN,
        UserRole.CLEANER,
        UserRole.SECURITY
    ]:

        await state.set_state(
            EmployeeCreateState.team
        )


        await message.answer(
            "Выберите команду:",
            reply_markup=teams_keyboard()
        )

    else:

        await finish_employee(
            message,
            state,
            None
        )



@router.message(
    EmployeeCreateState.team
)
async def get_team(
    message: Message,
    state: FSMContext
):

    teams = {

        "🔧 TEAM_TECH":
            Team.TEAM_TECH,

        "🧹 TEAM_CLEANING":
            Team.TEAM_CLEANING,

        "🛡 TEAM_SECURITY":
            Team.TEAM_SECURITY,

    }


    team = teams.get(
        message.text
    )


    if not team:

        await message.answer(
            "Выберите команду кнопкой"
        )

        return


    await finish_employee(
        message,
        state,
        team
    )



async def finish_employee(
    message,
    state,
    team
):

    data = await state.get_data()


    employee = await create_employee(

        full_name=data["full_name"],

        role=data["role"],

        team=team,

        phone=data["phone"]

    )


    await state.clear()


    await message.answer(

        f"✅ Сотрудник создан\n\n"

        f"👤 {employee.full_name}\n"

        f"Роль: {employee.role.value}\n\n"

        f"Код приглашения:\n"
        f"{employee.invite_code}"

    )
