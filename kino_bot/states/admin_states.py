from aiogram.fsm.state import State, StatesGroup


class AddMovie(StatesGroup):
    waiting_video = State()
    waiting_title = State()
    waiting_caption = State()


class DeleteMovie(StatesGroup):
    waiting_code = State()


class AddChannel(StatesGroup):
    waiting_channel = State()


class Broadcast(StatesGroup):
    waiting_message = State()
    confirming = State()


class ManageAdmin(StatesGroup):
    waiting_add_id = State()
    waiting_remove_id = State()


class SettingsState(StatesGroup):
    waiting_main_channel = State()
    waiting_sponsor_text = State()


class ManageUser(StatesGroup):
    waiting_block_id = State()
    waiting_unblock_id = State()
