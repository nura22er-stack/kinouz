import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from kino_bot.database.crud.admins import add_admin, is_admin, is_super_admin, remove_admin
from kino_bot.keyboards.admin_kb import admin_panel_keyboard
from kino_bot.states.admin_states import ManageAdmin
from kino_bot.texts import (
    ADMIN_ADDED,
    ADMIN_DENIED,
    ADMIN_REMOVED,
    ERROR_GENERIC,
    INVALID_ID,
    SEND_ADMIN_ID,
    SUPER_ADMIN_ONLY,
)

router = Router()
logger = logging.getLogger(__name__)


async def _super(user_id: int | None) -> bool:
    return bool(user_id and await is_super_admin(user_id))


@router.callback_query(F.data == "admin:add_admin")
async def ask_add_admin(callback: CallbackQuery, state) -> None:
    if not await _super(callback.from_user.id):
        await callback.answer(SUPER_ADMIN_ONLY, show_alert=True)
        return
    await callback.answer()
    await state.set_state(ManageAdmin.waiting_add_id)
    if callback.message:
        await callback.message.answer(SEND_ADMIN_ID)


@router.message(ManageAdmin.waiting_add_id)
async def save_admin(message: Message, state) -> None:
    try:
        if not await _super(message.from_user.id if message.from_user else None):
            await message.answer(SUPER_ADMIN_ONLY)
            return
        if not message.text or not message.text.strip().isdigit():
            await message.answer(INVALID_ID)
            return
        await add_admin(int(message.text.strip()), message.from_user.id)
        await state.clear()
        await message.answer(ADMIN_ADDED, reply_markup=admin_panel_keyboard())
    except Exception:
        logger.exception("Admin qo'shishda xatolik")
        await message.answer(ERROR_GENERIC)


@router.callback_query(F.data == "admin:remove_admin")
async def ask_remove_admin(callback: CallbackQuery, state) -> None:
    if not await _super(callback.from_user.id):
        await callback.answer(SUPER_ADMIN_ONLY, show_alert=True)
        return
    await callback.answer()
    await state.set_state(ManageAdmin.waiting_remove_id)
    if callback.message:
        await callback.message.answer(SEND_ADMIN_ID)


@router.message(ManageAdmin.waiting_remove_id)
async def delete_admin(message: Message, state) -> None:
    try:
        if not await _super(message.from_user.id if message.from_user else None):
            await message.answer(SUPER_ADMIN_ONLY)
            return
        if not message.text or not message.text.strip().isdigit():
            await message.answer(INVALID_ID)
            return
        ok = await remove_admin(int(message.text.strip()))
        await state.clear()
        text = ADMIN_REMOVED if ok else "Super-adminni yoki mavjud bo'lmagan adminni olib tashlab bo'lmaydi."
        await message.answer(text, reply_markup=admin_panel_keyboard())
    except Exception:
        logger.exception("Admin olib tashlashda xatolik")
        await message.answer(ERROR_GENERIC)
