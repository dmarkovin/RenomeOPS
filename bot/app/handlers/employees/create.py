from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext


from app.states.employees.create import (
    EmployeeCreateState,
)

from app.keyboards.employees.roles import (
    employee_roles_keyboard,
)

from app.database.models import (
    UserRole,
)

from app.services.employees.service import (
    create_employee,
)


router = Router()



@router.message(
    F.text == "👤 Новый сотрудник"
)
async def start_create_employee(
    message: Message,
    state: FSMContext,
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
async def employee_name(
    message: Message,
    state: FSMContext,
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
async def employee_phone(
    message: Message,
    state: FSMContext,
):

    await state.update_data(
        phone=message.text
    )


    await state.set_state(
        EmployeeCreateState.role
    )


    await message.answer(
        "Выберите должность:",
        reply_markup=employee_roles_keyboard()
    )
