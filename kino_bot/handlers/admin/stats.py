from aiogram import F, Router
from aiogram.types import CallbackQuery

from kino_bot.database.crud.admins import is_admin
from kino_bot.database.crud.channels import count_active_channels
from kino_bot.database.crud.movies import count_movies, top_movies
from kino_bot.database.crud.users import count_today_users, count_users
from kino_bot.keyboards.admin_kb import admin_panel_keyboard
from kino_bot.texts import ADMIN_DENIED

router = Router()


@router.callback_query(F.data == "admin:stats")
async def show_stats(callback: CallbackQuery) -> None:
    if not await is_admin(callback.from_user.id):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    await callback.answer()
    users_total = await count_users()
    users_today = await count_today_users()
    movies_total = await count_movies()
    channels_total = await count_active_channels()
    top = await top_movies()

    lines = [
        "Statistika",
        "",
        f"Jami foydalanuvchilar: {users_total}",
        f"Bugungi yangi foydalanuvchilar: {users_today}",
        f"Jami kinolar: {movies_total}",
        f"Faol majburiy kanallar: {channels_total}",
        "",
        "Top-5 kinolar:",
    ]
    if not top:
        lines.append("Hali kino yo'q.")
    for index, movie in enumerate(top, start=1):
        lines.append(f"{index}. {movie.code} - {movie.title} ({movie.views_count})")

    if callback.message:
        await callback.message.edit_text(
            "\n".join(lines), reply_markup=admin_panel_keyboard()
        )
