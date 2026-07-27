from aiogram.fsm.state import State, StatesGroup

class TaskContext(StatesGroup):
    sort_by = State()  # date или priority
    filter_priority = State()  # None или число (1-5)
    list_type = State()  # 'open', 'my', 'team', 'checking', 'archive'
    page = State()
