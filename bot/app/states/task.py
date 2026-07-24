from aiogram.fsm.state import StatesGroup, State


class TaskCreate(StatesGroup):

    title = State()

    description = State()

    category = State()

    priority = State()

    object = State()

    location = State()

    deadline = State()

    confirmation = State()
