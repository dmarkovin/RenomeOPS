from aiogram.fsm.state import State, StatesGroup

class TaskContext(StatesGroup):
    list_type = State()  # 'open', 'my', 'team', 'checking', 'archive'
    page = State()
