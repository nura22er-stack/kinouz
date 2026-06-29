import logging

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from kino_bot.database.crud.admins import is_admin
from kino_bot.database.crud.movies import (
    create_movie,
    delete_movie_by_code,
    list_movies,
    update_channel_message_id,
)
from kino_bot.keyboards.admin_kb import admin_panel_keyboard, movie_pages_keyboard, skip_keyboard
from kino_bot.states.admin_states import AddMovie, DeleteMovie
from kino_bot.texts import (
    ADMIN_DENIED,
    ERROR_GENERIC,
    MOVIE_ADDED,
    MOVIE_DELETED,
    SEND_CAPTION,
    SEND_DELETE_CODE,
    SEND_PHOTO,
    SEND_TITLE,
    SEND_VIDEO,
    SKIP,
)
from kino_bot.utils.channel_poster import post_movie_to_channel
from kino_bot.utils.code_generator import make_unique_movie_code

router = Router()
logger = logging.getLogger(__name__)


async def _admin(user_id: int | None) -> bool:
    return bool(user_id and await is_admin(user_id))


@router.callback_query(F.data == "admin:add_movie")
async def add_movie_start(callback: CallbackQuery, state) -> None:
    if not await _admin(callback.from_user.id):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    await callback.answer()
    await state.set_state(AddMovie.waiting_photo)
    if callback.message:
        await callback.message.answer(SEND_PHOTO)


@router.message(AddMovie.waiting_photo, F.photo)
async def add_movie_photo(message: Message, state) -> None:
    if not await _admin(message.from_user.id if message.from_user else None):
        await message.answer(ADMIN_DENIED)
        return
    await state.update_data(poster_file_id=message.photo[-1].file_id)
    await state.set_state(AddMovie.waiting_video)
    await message.answer(SEND_VIDEO)


@router.message(AddMovie.waiting_photo)
async def add_movie_photo_invalid(message: Message) -> None:
    await message.answer(SEND_PHOTO)


@router.message(AddMovie.waiting_video, F.video)
async def add_movie_video(message: Message, state) -> None:
    if not await _admin(message.from_user.id if message.from_user else None):
        await message.answer(ADMIN_DENIED)
        return
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(AddMovie.waiting_title)
    await message.answer(SEND_TITLE)


@router.message(AddMovie.waiting_video)
async def add_movie_video_invalid(message: Message) -> None:
    await message.answer(SEND_VIDEO)


@router.message(AddMovie.waiting_title)
async def add_movie_title(message: Message, state) -> None:
    if not await _admin(message.from_user.id if message.from_user else None):
        await message.answer(ADMIN_DENIED)
        return
    title = (message.text or "").strip()
    if not title:
        await message.answer(SEND_TITLE)
        return
    await state.update_data(title=title)
    await state.set_state(AddMovie.waiting_caption)
    await message.answer(SEND_CAPTION, reply_markup=skip_keyboard())


@router.message(AddMovie.waiting_caption)
async def add_movie_caption(message: Message, bot: Bot, state) -> None:
    try:
        if not await _admin(message.from_user.id if message.from_user else None):
            await message.answer(ADMIN_DENIED)
            return
        data = await state.get_data()
        caption = None if (message.text or "") == SKIP else message.text
        code = await make_unique_movie_code()
        channel_message_id = await post_movie_to_channel(
            bot=bot,
            poster_file_id=data.get("poster_file_id"),
            file_id=data["file_id"],
            title=data["title"],
            code=code,
            caption=caption,
        )
        await create_movie(
            code=code,
            title=data["title"],
            file_id=data["file_id"],
            caption=caption,
            added_by=message.from_user.id,
            poster_file_id=data.get("poster_file_id"),
            channel_message_id=channel_message_id,
        )
        if channel_message_id:
            await update_channel_message_id(code, channel_message_id)
        await state.clear()
        await message.answer(
            MOVIE_ADDED.format(code=code),
            reply_markup=ReplyKeyboardRemove(),
        )
    except Exception:
        logger.exception("Kino qo'shishda xatolik")
        await message.answer(ERROR_GENERIC, reply_markup=ReplyKeyboardRemove())


@router.callback_query(F.data == "admin:delete_movie")
async def ask_delete_movie(callback: CallbackQuery, state) -> None:
    if not await _admin(callback.from_user.id):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    await callback.answer()
    await state.set_state(DeleteMovie.waiting_code)
    if callback.message:
        await callback.message.answer(SEND_DELETE_CODE)


@router.message(DeleteMovie.waiting_code)
async def delete_movie(message: Message, bot: Bot, state) -> None:
    try:
        if not await _admin(message.from_user.id if message.from_user else None):
            await message.answer(ADMIN_DENIED)
            return
        movie = await delete_movie_by_code((message.text or "").strip())
        if not movie:
            await message.answer("Kino topilmadi.")
            return
        if movie.channel_message_id:
            try:
                from kino_bot.database.crud.settings import get_setting

                main_channel_id = await get_setting("main_channel_id")
                if main_channel_id:
                    await bot.delete_message(main_channel_id, movie.channel_message_id)
            except Exception:
                logger.warning("Kanaldagi post o'chirilmadi", exc_info=True)
        await state.clear()
        await message.answer(MOVIE_DELETED, reply_markup=admin_panel_keyboard())
    except Exception:
        logger.exception("Kino o'chirishda xatolik")
        await message.answer(ERROR_GENERIC)


@router.callback_query(F.data.startswith("admin:list_movies:"))
async def movies_list(callback: CallbackQuery) -> None:
    if not await _admin(callback.from_user.id):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    await callback.answer()
    page = int((callback.data or "admin:list_movies:1").split(":")[-1])
    movies, total = await list_movies(page)
    lines = [f"Kinolar ro'yxati ({page}-sahifa):", ""]
    if not movies:
        lines.append("Kino yo'q.")
    for movie in movies:
        lines.append(f"{movie.code} - {movie.title} | ko'rishlar: {movie.views_count}")
    if callback.message:
        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=movie_pages_keyboard(page, total),
        )
