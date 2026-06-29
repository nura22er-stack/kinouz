import logging

from aiogram import Bot, F, Router
from aiogram.types import Message

from kino_bot.database.crud.movies import get_movie_by_code, increment_views
from kino_bot.database.crud.settings import get_setting
from kino_bot.texts import ERROR_GENERIC, MOVIE_NOT_FOUND

router = Router()
logger = logging.getLogger(__name__)


async def send_movie_by_code(message: Message, bot: Bot, code: str) -> None:
    try:
        movie = await get_movie_by_code(code.strip())
        if not movie:
            await message.answer(MOVIE_NOT_FOUND)
            return

        sponsor_text = await get_setting("sponsor_text", "")
        caption_parts = [f"🎬 <b>{movie.title}</b>", f"🔑 Kod: <code>{movie.code}</code>"]
        if movie.caption:
            caption_parts.append(movie.caption)
        if sponsor_text:
            caption_parts.append(sponsor_text)

        await bot.send_video(
            chat_id=message.chat.id,
            video=movie.file_id,
            caption="\n\n".join(caption_parts),
        )
        await increment_views(movie.code)
    except Exception:
        logger.exception("Kino yuborishda xatolik")
        await message.answer(ERROR_GENERIC)


@router.message(F.text.regexp(r"^\d+$"))
async def get_movie(message: Message, bot: Bot) -> None:
    await send_movie_by_code(message, bot, message.text or "")
