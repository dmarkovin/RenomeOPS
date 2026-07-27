from aiogram.fsm.state import StatesGroup, State

class TaskAddPhoto(StatesGroup):
    waiting_for_photo = State()
