from aiogram.fsm.state import StatesGroup, State

class Register(StatesGroup):
    nickname = State()
