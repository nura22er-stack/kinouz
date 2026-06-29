from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [("🎬 Kino qo'shish", "admin:add_movie"), ("📃 Kinolar ro'yxati", "admin:list_movies:1")],
        [("🗑 Kino o'chirish", "admin:delete_movie"), ("📊 Statistika", "admin:stats")],
        [("📢 Kanal qo'shish", "admin:add_channel"), ("📋 Kanallar ro'yxati", "admin:list_channels")],
        [("➖ Kanal o'chirish", "admin:delete_channel"), ("✉️ Xabar yuborish", "admin:broadcast")],
        [("👤 Admin qo'shish", "admin:add_admin"), ("🚫 Adminni olib tashlash", "admin:remove_admin")],
        [("👥 Foydalanuvchilar", "admin:users"), ("⚙️ Sozlamalar", "admin:settings")],
        [("🔙 Yopish", "admin:close")],
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=data) for text, data in row]
            for row in rows
        ]
    )


def skip_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="O'tkazib yuborish")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def confirm_keyboard(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha", callback_data=f"{prefix}:yes"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data=f"{prefix}:no"),
            ]
        ]
    )


def movie_pages_keyboard(page: int, total: int, per_page: int = 10) -> InlineKeyboardMarkup:
    buttons: list[InlineKeyboardButton] = []
    if page > 1:
        buttons.append(
            InlineKeyboardButton(
                text="⬅️ Oldingi", callback_data=f"admin:list_movies:{page - 1}"
            )
        )
    if page * per_page < total:
        buttons.append(
            InlineKeyboardButton(
                text="Keyingi ➡️", callback_data=f"admin:list_movies:{page + 1}"
            )
        )
    rows = [buttons] if buttons else []
    rows.append([InlineKeyboardButton(text="🔙 Panel", callback_data="admin:panel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def channel_list_keyboard(
    channels: list[tuple[int, str]], delete: bool = False
) -> InlineKeyboardMarkup:
    rows = []
    for channel_id, title in channels:
        data = f"admin:remove_channel:{channel_id}" if delete else "admin:noop"
        rows.append([InlineKeyboardButton(text=title, callback_data=data)])
    rows.append([InlineKeyboardButton(text="🔙 Panel", callback_data="admin:panel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Asosiy kanal", callback_data="admin:set_main_channel")],
            [InlineKeyboardButton(text="🤝 Sponsor matni", callback_data="admin:set_sponsor_text")],
            [InlineKeyboardButton(text="🔙 Panel", callback_data="admin:panel")],
        ]
    )
