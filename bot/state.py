from aiogram.fsm.state import State, StatesGroup


class State_settings(StatesGroup):
    token = State()
    low = State()
    high = State()
