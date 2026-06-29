import logging

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from kino_bot.database.crud.settings import get_setting

logger = logging.getLogger(__name__)


async def post_movie_to_channel(
    bot: Bot,
    poster_file_id: str | None,
    file_id: str,
    title: str,
    code: str,
    caption: str | None = None,
) -> int | None:
    main_channel_id = await get_setting("main_channel_id")
    if not main_channel_id:
        return None

    bot_info = await bot.get_me()
    deep_link = f"https://t.me/{bot_info.username}?start={code}"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Botda tomosha qilish", url=deep_link)]
        ]
    )

    caption_parts = [f"🎬 <b>{title}</b>", f"🔑 Kod: <code>{code}</code>"]
    if caption:
        caption_parts.append(caption)
    channel_caption = "\n\n".join(caption_parts)

    try:
        if poster_file_id:
            message = await bot.send_photo(
                chat_id=main_channel_id,
                photo=poster_file_id,
                caption=channel_caption,
                reply_markup=keyboard,
            )
        else:
            message = await bot.send_video(
                chat_id=main_channel_id,
                video=file_id,
                caption=channel_caption,
                reply_markup=keyboard,
            )
        return message.message_id
    except Exception:
        logger.exception("Kino kanalga post qilinmadi")
        return None
