import logging

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from kino_bot.database.crud.admins import is_admin
from kino_bot.database.crud.channels import add_channel, all_channels, deactivate_channel
from kino_bot.keyboards.admin_kb import admin_panel_keyboard, channel_list_keyboard
from kino_bot.states.admin_states import AddChannel
from kino_bot.texts import (
    ADMIN_DENIED,
    CHANNEL_ADDED,
    CHANNEL_ADMIN_REQUIRED,
    CHANNEL_SEND,
    ERROR_GENERIC,
)

router = Router()
logger = logging.getLogger(__name__)


async def _admin(user_id: int | None) -> bool:
    return bool(user_id and await is_admin(user_id))


@router.callback_query(F.data == "admin:add_channel")
async def ask_channel(callback: CallbackQuery, state) -> None:
    if not await _admin(callback.from_user.id):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    await callback.answer()
    await state.set_state(AddChannel.waiting_channel)
    if callback.message:
        await callback.message.answer(CHANNEL_SEND)


@router.message(AddChannel.waiting_channel)
async def save_channel(message: Message, bot: Bot, state) -> None:
    try:
        if not await _admin(message.from_user.id if message.from_user else None):
            await message.answer(ADMIN_DENIED)
            return
        raw_chat_id = (message.text or "").strip()
        if not raw_chat_id:
            await message.answer(CHANNEL_SEND)
            return
        chat = await bot.get_chat(raw_chat_id)
        bot_info = await bot.get_me()
        bot_member = await bot.get_chat_member(chat.id, bot_info.id)
        if bot_member.status not in {"administrator", "creator"}:
            await message.answer(CHANNEL_ADMIN_REQUIRED)
            return

        invite_link = chat.invite_link
        if not invite_link and not chat.username:
            try:
                invite_link = await bot.create_chat_invite_link(chat.id)
                invite_link = invite_link.invite_link
            except Exception:
                logger.warning("Invite link yaratilmadi", exc_info=True)

        await add_channel(
            chat_id=str(chat.id),
            title=chat.title or raw_chat_id,
            username=f"@{chat.username}" if chat.username else None,
            invite_link=invite_link,
            added_by=message.from_user.id,
        )
        await state.clear()
        await message.answer(CHANNEL_ADDED, reply_markup=admin_panel_keyboard())
    except Exception:
        logger.exception("Kanal qo'shishda xatolik")
        await message.answer(ERROR_GENERIC)


@router.callback_query(F.data == "admin:list_channels")
async def list_channels(callback: CallbackQuery) -> None:
    if not await _admin(callback.from_user.id):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    await callback.answer()
    channels = await all_channels()
    lines = ["Kanallar ro'yxati:", ""]
    if not channels:
        lines.append("Kanal yo'q.")
    for channel in channels:
        status = "faol" if channel.is_active else "o'chirilgan"
        lines.append(f"{channel.id}. {channel.title} - {status}")
    if callback.message:
        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=channel_list_keyboard(
                [(channel.id, channel.title) for channel in channels]
            ),
        )


@router.callback_query(F.data == "admin:delete_channel")
async def choose_delete_channel(callback: CallbackQuery) -> None:
    if not await _admin(callback.from_user.id):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    await callback.answer()
    channels = [channel for channel in await all_channels() if channel.is_active]
    if callback.message:
        await callback.message.edit_text(
            "O'chiriladigan kanalni tanlang:",
            reply_markup=channel_list_keyboard(
                [(channel.id, channel.title) for channel in channels], delete=True
            ),
        )


@router.callback_query(F.data.startswith("admin:remove_channel:"))
async def remove_channel(callback: CallbackQuery) -> None:
    if not await _admin(callback.from_user.id):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    channel_id = int((callback.data or "").split(":")[-1])
    await deactivate_channel(channel_id)
    await callback.answer("Kanal o'chirildi.")
    if callback.message:
        await callback.message.edit_text(
            "Kanal o'chirildi.", reply_markup=admin_panel_keyboard()
        )
