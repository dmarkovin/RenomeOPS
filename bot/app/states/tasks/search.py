from aiogram.fsm.state import StatesGroup, State

class TaskSearch(StatesGroup):
    query = State()
