from aiogram.fsm.state import StatesGroup, State

class Feedback(StatesGroup):
    text = State()
    photo = State()
