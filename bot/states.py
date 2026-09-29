from aiogram.fsm.state import State, StatesGroup


class OrderFSM(StatesGroup):
    waiting_for_instruction_ack = State()
    waiting_for_dimensions = State()
    waiting_for_photos = State()
    waiting_for_color = State()
    waiting_for_custom_color_code = State()
    waiting_for_country = State()
    waiting_for_address = State()
    waiting_for_contact = State()
    waiting_for_confirmation = State()
