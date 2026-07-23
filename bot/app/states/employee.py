from aiogram.fsm.state import StatesGroup, State


class EmployeeRegistration(StatesGroup):

    full_name = State()

    phone = State()

    role = State()

    team = State()
