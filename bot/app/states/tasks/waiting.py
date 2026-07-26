from aiogram.fsm.state import StatesGroup, State

class TaskWaiting(StatesGroup):
    comment = State()
