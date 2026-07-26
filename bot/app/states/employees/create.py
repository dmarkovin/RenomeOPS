from aiogram.fsm.state import State, StatesGroup


class EmployeeCreateState(StatesGroup):

    full_name = State()

    phone = State()

    role = State()

    team = State()
