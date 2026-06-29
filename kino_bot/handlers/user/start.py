import logging
from html import escape

from aiogram import Bot, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message

from kino_bot.database.crud.users import upsert_user
from kino_bot.handlers.user.get_movie import send_movie_by_code
from kino_bot.texts import ERROR_GENERIC, SUBSCRIBE_SUCCESS, WELCOME

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def start(message: Message, bot: Bot, command: CommandObject) -> None:
    try:
        if message.from_user:
            await upsert_user(
                telegram_id=message.from_user.id,
                full_name=message.from_user.full_name,
                username=message.from_user.username,
            )
        if command.args:
            await send_movie_by_code(message, bot, command.args)
            return
        name = (
            escape(message.from_user.full_name)
            if message.from_user
            else "aziz foydalanuvchi"
        )
        await message.answer(WELCOME.format(name=name))
    except Exception:
        logger.exception("/start handler xatoligi")
        await message.answer(ERROR_GENERIC)


@router.callback_query(lambda call: call.data and call.data.startswith("check_sub"))
async def check_sub(callback: CallbackQuery, bot: Bot) -> None:
    try:
        await callback.answer()
        if not callback.message:
            return
        parts = (callback.data or "").split(":", maxsplit=1)
        if len(parts) == 2 and parts[1]:
            await send_movie_by_code(callback.message, bot, parts[1])
        else:
            await callback.message.answer(SUBSCRIBE_SUCCESS)
    except Exception:
        logger.exception("Obunani qayta tekshirishda xatolik")
        if callback.message:
            await callback.message.answer(ERROR_GENERIC)
