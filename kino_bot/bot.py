import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from kino_bot.config import settings
from kino_bot.database.crud.admins import ensure_super_admins
from kino_bot.database.crud.settings import set_setting
from kino_bot.database.engine import close_db, init_db
from kino_bot.handlers.admin import admins_manage, broadcast, channels, movies, panel, stats
from kino_bot.handlers.user import get_movie, start
from kino_bot.middlewares.force_sub import ForceSubMiddleware


def setup_logging() -> None:
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)

    file_handler = RotatingFileHandler(
        settings.log_file, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


async def main() -> None:
    setup_logging()
    await init_db()
    await ensure_super_admins(settings.admin_ids)
    if settings.main_channel_id:
        await set_setting("main_channel_id", settings.main_channel_id)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    force_sub = ForceSubMiddleware()
    dp.message.middleware(force_sub)
    dp.callback_query.middleware(force_sub)

    dp.include_router(panel.router)
    dp.include_router(movies.router)
    dp.include_router(channels.router)
    dp.include_router(broadcast.router)
    dp.include_router(admins_manage.router)
    dp.include_router(stats.router)
    dp.include_router(start.router)
    dp.include_router(get_movie.router)

    logging.info("Bot polling rejimida ishga tushdi")
    try:
        await dp.start_polling(bot)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
