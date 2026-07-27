from aiogram.fsm.state import StatesGroup, State

class RoleChange(StatesGroup):
    select_role = State()
    reason = State()
