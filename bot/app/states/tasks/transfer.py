from aiogram.fsm.state import StatesGroup, State

class TaskTransfer(StatesGroup):
    select_employee = State()
    comment = State()
