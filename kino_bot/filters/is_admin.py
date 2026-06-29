from aiogram.filters import BaseFilter
from aiogram.types import Message

from kino_bot.database.crud.admins import is_admin


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return bool(message.from_user and await is_admin(message.from_user.id))
