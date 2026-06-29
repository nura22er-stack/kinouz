from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from kino_bot.database.crud.admins import is_admin
from kino_bot.texts import ADMIN_DENIED


class AdminOnlyMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.from_user:
            if await is_admin(event.from_user.id):
                return await handler(event, data)
            await event.answer(ADMIN_DENIED)
            return None
        return await handler(event, data)
