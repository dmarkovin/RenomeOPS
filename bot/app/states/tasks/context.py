from aiogram.fsm.state import StatesGroup, State

class TaskContext(StatesGroup):
    list_type = State()
    selected_team = State()  # хранит выбранную команду для фильтрации в списке заявок
