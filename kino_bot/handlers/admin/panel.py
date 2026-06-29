import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from kino_bot.database.crud.admins import is_admin
from kino_bot.database.crud.settings import set_setting
from kino_bot.database.crud.users import count_users, latest_users, set_user_blocked
from kino_bot.keyboards.admin_kb import admin_panel_keyboard, settings_keyboard
from kino_bot.states.admin_states import ManageUser, SettingsState
from kino_bot.texts import (
    ADMIN_DENIED,
    ADMIN_PANEL,
    ERROR_GENERIC,
    INVALID_ID,
    MAIN_CHANNEL_SAVED,
    SEND_MAIN_CHANNEL,
    SEND_SPONSOR_TEXT,
    SPONSOR_TEXT_SAVED,
)

router = Router()
logger = logging.getLogger(__name__)


async def _ensure_admin(user_id: int | None) -> bool:
    return bool(user_id and await is_admin(user_id))


@router.message(Command("admin"))
async def admin_panel(message: Message) -> None:
    try:
        if not await _ensure_admin(message.from_user.id if message.from_user else None):
            await message.answer(ADMIN_DENIED)
            return
        await message.answer(ADMIN_PANEL, reply_markup=admin_panel_keyboard())
    except Exception:
        logger.exception("Admin panel xatoligi")
        await message.answer(ERROR_GENERIC)


@router.callback_query(F.data == "admin:panel")
async def admin_panel_callback(callback: CallbackQuery) -> None:
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(ADMIN_PANEL, reply_markup=admin_panel_keyboard())


@router.callback_query(F.data == "admin:close")
async def close_panel(callback: CallbackQuery) -> None:
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    await callback.answer()
    if callback.message:
        await callback.message.delete()


@router.callback_query(F.data == "admin:settings")
async def settings_menu(callback: CallbackQuery) -> None:
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    await callback.answer()
    if callback.message:
        await callback.message.edit_text("Sozlamalar:", reply_markup=settings_keyboard())


@router.callback_query(F.data == "admin:set_main_channel")
async def ask_main_channel(callback: CallbackQuery, state) -> None:
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    await callback.answer()
    await state.set_state(SettingsState.waiting_main_channel)
    if callback.message:
        await callback.message.answer(SEND_MAIN_CHANNEL)


@router.message(SettingsState.waiting_main_channel)
async def save_main_channel(message: Message, state) -> None:
    try:
        if not await _ensure_admin(message.from_user.id if message.from_user else None):
            await message.answer(ADMIN_DENIED)
            return
        await set_setting("main_channel_id", message.text.strip() if message.text else "")
        await state.clear()
        await message.answer(MAIN_CHANNEL_SAVED, reply_markup=admin_panel_keyboard())
    except Exception:
        logger.exception("Asosiy kanal saqlash xatoligi")
        await message.answer(ERROR_GENERIC)


@router.callback_query(F.data == "admin:set_sponsor_text")
async def ask_sponsor_text(callback: CallbackQuery, state) -> None:
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    await callback.answer()
    await state.set_state(SettingsState.waiting_sponsor_text)
    if callback.message:
        await callback.message.answer(SEND_SPONSOR_TEXT)


@router.message(SettingsState.waiting_sponsor_text)
async def save_sponsor_text(message: Message, state) -> None:
    try:
        if not await _ensure_admin(message.from_user.id if message.from_user else None):
            await message.answer(ADMIN_DENIED)
            return
        await set_setting("sponsor_text", message.text or "")
        await state.clear()
        await message.answer(SPONSOR_TEXT_SAVED, reply_markup=admin_panel_keyboard())
    except Exception:
        logger.exception("Sponsor matni saqlash xatoligi")
        await message.answer(ERROR_GENERIC)


@router.callback_query(F.data == "admin:users")
async def users_info(callback: CallbackQuery) -> None:
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    await callback.answer()
    total = await count_users()
    users = await latest_users(10)
    lines = [f"Jami foydalanuvchilar: {total}", "", "Oxirgi qo'shilganlar:"]
    for user in users:
        name = user.full_name or "Nomsiz"
        status = "bloklangan" if user.is_blocked else "faol"
        lines.append(f"{user.telegram_id} - {name} ({status})")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Bloklash", callback_data="admin:block_user")],
            [InlineKeyboardButton(text="Blokdan chiqarish", callback_data="admin:unblock_user")],
            [InlineKeyboardButton(text="Panel", callback_data="admin:panel")],
        ]
    )
    if callback.message:
        await callback.message.edit_text("\n".join(lines), reply_markup=keyboard)


@router.callback_query(F.data == "admin:block_user")
async def ask_block_user(callback: CallbackQuery, state) -> None:
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    await callback.answer()
    await state.set_state(ManageUser.waiting_block_id)
    if callback.message:
        await callback.message.answer("Bloklanadigan foydalanuvchi Telegram ID sini yuboring.")


@router.callback_query(F.data == "admin:unblock_user")
async def ask_unblock_user(callback: CallbackQuery, state) -> None:
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    await callback.answer()
    await state.set_state(ManageUser.waiting_unblock_id)
    if callback.message:
        await callback.message.answer("Blokdan chiqariladigan foydalanuvchi Telegram ID sini yuboring.")


@router.message(ManageUser.waiting_block_id)
async def block_user(message: Message, state) -> None:
    if not await _ensure_admin(message.from_user.id if message.from_user else None):
        await message.answer(ADMIN_DENIED)
        return
    if not message.text or not message.text.strip().isdigit():
        await message.answer(INVALID_ID)
        return
    ok = await set_user_blocked(int(message.text.strip()), True)
    await state.clear()
    text = "Foydalanuvchi bloklandi." if ok else "Foydalanuvchi topilmadi."
    await message.answer(text, reply_markup=admin_panel_keyboard())


@router.message(ManageUser.waiting_unblock_id)
async def unblock_user(message: Message, state) -> None:
    if not await _ensure_admin(message.from_user.id if message.from_user else None):
        await message.answer(ADMIN_DENIED)
        return
    if not message.text or not message.text.strip().isdigit():
        await message.answer(INVALID_ID)
        return
    ok = await set_user_blocked(int(message.text.strip()), False)
    await state.clear()
    text = "Foydalanuvchi blokdan chiqarildi." if ok else "Foydalanuvchi topilmadi."
    await message.answer(text, reply_markup=admin_panel_keyboard())
