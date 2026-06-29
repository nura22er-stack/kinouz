import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import CallbackQuery, Message

from kino_bot.database.crud.admins import is_admin
from kino_bot.database.crud.users import get_all_users, set_user_blocked
from kino_bot.database.engine import SessionLocal
from kino_bot.database.models import BroadcastLog
from kino_bot.keyboards.admin_kb import admin_panel_keyboard, confirm_keyboard
from kino_bot.states.admin_states import Broadcast
from kino_bot.texts import (
    ADMIN_DENIED,
    BROADCAST_CONFIRM,
    BROADCAST_DONE,
    BROADCAST_SEND,
    ERROR_GENERIC,
)

router = Router()
logger = logging.getLogger(__name__)


async def _admin(user_id: int | None) -> bool:
    return bool(user_id and await is_admin(user_id))


@router.callback_query(F.data == "admin:broadcast")
async def ask_broadcast(callback: CallbackQuery, state) -> None:
    if not await _admin(callback.from_user.id):
        await callback.answer(ADMIN_DENIED, show_alert=True)
        return
    await callback.answer()
    await state.set_state(Broadcast.waiting_message)
    if callback.message:
        await callback.message.answer(BROADCAST_SEND)


@router.message(Broadcast.waiting_message)
async def receive_broadcast(message: Message, state) -> None:
    if not await _admin(message.from_user.id if message.from_user else None):
        await message.answer(ADMIN_DENIED)
        return
    await state.update_data(chat_id=message.chat.id, message_id=message.message_id)
    await state.set_state(Broadcast.confirming)
    await message.answer(BROADCAST_CONFIRM, reply_markup=confirm_keyboard("broadcast_confirm"))


@router.callback_query(F.data.startswith("broadcast_confirm:"))
async def confirm_broadcast(callback: CallbackQuery, bot: Bot, state) -> None:
    try:
        if not await _admin(callback.from_user.id):
            await callback.answer(ADMIN_DENIED, show_alert=True)
            return
        decision = (callback.data or "").split(":")[-1]
        if decision != "yes":
            await state.clear()
            await callback.answer("Bekor qilindi.")
            if callback.message:
                await callback.message.answer("Bekor qilindi.", reply_markup=admin_panel_keyboard())
            return

        data = await state.get_data()
        users = await get_all_users()
        sent = 0
        failed = 0
        for user in users:
            try:
                await bot.copy_message(
                    chat_id=user.telegram_id,
                    from_chat_id=data["chat_id"],
                    message_id=data["message_id"],
                )
                sent += 1
            except TelegramForbiddenError:
                await set_user_blocked(user.telegram_id, True)
                failed += 1
            except Exception:
                logger.warning("Broadcast yuborilmadi: %s", user.telegram_id, exc_info=True)
                failed += 1
            await asyncio.sleep(0.025)

        async with SessionLocal() as session:
            session.add(
                BroadcastLog(
                    admin_id=callback.from_user.id,
                    text="copy_message",
                    sent_count=sent,
                    failed_count=failed,
                )
            )
            await session.commit()
        await state.clear()
        if callback.message:
            await callback.message.answer(
                BROADCAST_DONE.format(sent=sent, failed=failed),
                reply_markup=admin_panel_keyboard(),
            )
    except Exception:
        logger.exception("Broadcast xatoligi")
        if callback.message:
            await callback.message.answer(ERROR_GENERIC)
