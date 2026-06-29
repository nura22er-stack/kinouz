import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware, Bot
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import CallbackQuery, Message, TelegramObject

from kino_bot.config import settings
from kino_bot.database.crud.admins import ensure_super_admin, is_admin
from kino_bot.database.crud.channels import active_channels
from kino_bot.database.crud.users import get_user, upsert_user
from kino_bot.keyboards.user_kb import force_sub_keyboard
from kino_bot.texts import SUBSCRIBE_FAILED, SUBSCRIBE_REQUIRED, USER_BLOCKED

logger = logging.getLogger(__name__)


class ForceSubMiddleware(BaseMiddleware):
    def __init__(self, ttl: int = 60) -> None:
        self.ttl = ttl
        self.cache: dict[int, tuple[float, bool]] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = None
        pending_code = None
        force_refresh = False

        if isinstance(event, Message):
            user = event.from_user
            if event.text and event.text.startswith("/start "):
                pending_code = event.text.split(maxsplit=1)[1].strip()
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            if event.data and event.data.startswith("check_sub"):
                force_refresh = True
                parts = event.data.split(":", maxsplit=1)
                pending_code = parts[1] if len(parts) == 2 else None

        if not user:
            return await handler(event, data)

        username = (user.username or "").lower()
        if username and username in settings.admin_usernames:
            await ensure_super_admin(user.id)
            return await handler(event, data)

        if await is_admin(user.id):
            return await handler(event, data)

        try:
            db_user = await upsert_user(user.id, user.full_name, user.username)
        except Exception:
            logger.exception("Foydalanuvchini DB'ga yozishda xatolik")
            db_user = await get_user(user.id)

        if db_user and db_user.is_blocked:
            if isinstance(event, CallbackQuery):
                await event.answer(USER_BLOCKED, show_alert=True)
            elif isinstance(event, Message):
                await event.answer(USER_BLOCKED)
            return None

        bot: Bot = data["bot"]
        channels = await active_channels()
        if not channels:
            return await handler(event, data)

        subscribed = await self._is_subscribed(
            bot=bot,
            user_id=user.id,
            channels=channels,
            force_refresh=force_refresh,
        )
        if subscribed:
            return await handler(event, data)

        keyboard = force_sub_keyboard(channels, pending_code)
        if isinstance(event, CallbackQuery):
            await event.answer(SUBSCRIBE_FAILED, show_alert=True)
            if event.message:
                await event.message.answer(SUBSCRIBE_REQUIRED, reply_markup=keyboard)
            return None

        await event.answer(SUBSCRIBE_REQUIRED, reply_markup=keyboard)
        return None

    async def _is_subscribed(
        self,
        bot: Bot,
        user_id: int,
        channels: list[Any],
        force_refresh: bool = False,
    ) -> bool:
        cached = self.cache.get(user_id)
        if cached and not force_refresh and time.time() - cached[0] < self.ttl:
            return cached[1]

        results = await asyncio.gather(
            *[self._check_one(bot, user_id, channel.chat_id) for channel in channels],
            return_exceptions=True,
        )
        subscribed = all(result is True for result in results)
        self.cache[user_id] = (time.time(), subscribed)
        return subscribed

    async def _check_one(self, bot: Bot, user_id: int, chat_id: str) -> bool:
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            return member.status in {"creator", "administrator", "member"}
        except TelegramForbiddenError:
            return False
        except Exception:
            logger.exception("Force-sub tekshiruvida xatolik: chat_id=%s", chat_id)
            return False
