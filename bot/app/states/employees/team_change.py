from aiogram.fsm.state import StatesGroup, State

class TeamChange(StatesGroup):
    select_team = State()
    reason = State()
