from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from kino_bot.database.models import ForceSubChannel
from kino_bot.texts import SUBSCRIBE_BUTTON


def force_sub_keyboard(
    channels: list[ForceSubChannel], pending_code: str | None = None
) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    for channel in channels:
        link = channel.invite_link or (
            f"https://t.me/{channel.username.lstrip('@')}" if channel.username else None
        )
        if link:
            buttons.append([InlineKeyboardButton(text=channel.title, url=link)])
    callback_data = "check_sub"
    if pending_code:
        callback_data = f"check_sub:{pending_code}"
    buttons.append([InlineKeyboardButton(text=SUBSCRIBE_BUTTON, callback_data=callback_data)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
