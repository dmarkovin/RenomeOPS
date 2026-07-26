from aiogram.fsm.state import StatesGroup, State


class EmployeeRegistration(StatesGroup):
    full_name = State()   # ФИО
    phone = State()       # телефон
    role = State()        # выбор роли
    team = State()        # выбор команды (если применимо)
    confirm = State()     # подтверждение перед созданием
