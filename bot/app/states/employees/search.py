from aiogram.fsm.state import StatesGroup, State

class EmployeeSearch(StatesGroup):
    query = State()
