"""Admin broadcast (mailing): send any message — text (with formatting), photo/video with
caption, voice message, video note (circle), etc. — to every registered user.

Uses bot.copy_message from the admin's own message, which preserves formatting entities,
media, and captions generically without needing to special-case each content type.
"""
import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import config
import keyboards
import messages
from database import Database
from states import AdminStates
from utils.helpers import is_admin

router = Router(name="broadcast")
logger = logging.getLogger("trading_bot")


@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.set_state(AdminStates.broadcast_waiting_content)
    await callback.message.answer(
        messages.format_message("broadcast_prompt"),
        reply_markup=keyboards.get_broadcast_prompt_keyboard(),
    )
    await callback.answer()


@router.message(AdminStates.broadcast_waiting_content)
async def on_broadcast_content_received(message: Message, state: FSMContext) -> None:
    await state.update_data(broadcast_chat_id=message.chat.id, broadcast_message_id=message.message_id)
    await state.set_state(AdminStates.broadcast_confirm)
    await message.answer(
        messages.format_message("broadcast_preview_prompt"),
        reply_markup=keyboards.get_broadcast_confirm_keyboard(),
    )


@router.callback_query(F.data == "broadcast_cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.clear()
    await callback.message.edit_text(messages.format_message("broadcast_cancelled"))
    await callback.answer()


@router.callback_query(F.data == "broadcast_confirm")
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext, db: Database, bot: Bot) -> None:
    admin_id = callback.from_user.id
    if not is_admin(admin_id):
        await callback.answer()
        return

    data = await state.get_data()
    from_chat_id = data.get("broadcast_chat_id")
    message_id = data.get("broadcast_message_id")
    await state.clear()

    if from_chat_id is None or message_id is None:
        await callback.answer(messages.format_message("decision_not_found"), show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_text(messages.format_message("broadcast_started"))

    users = await db.get_all_users()
    sent = 0
    failed = 0
    for user in users:
        try:
            await bot.copy_message(chat_id=user["user_id"], from_chat_id=from_chat_id, message_id=message_id)
            sent += 1
        except Exception:
            failed += 1
            logger.warning("Broadcast failed for user_id=%s", user["user_id"], exc_info=True)
        if config.BROADCAST_DELAY_SECONDS:
            await asyncio.sleep(config.BROADCAST_DELAY_SECONDS)

    await bot.send_message(
        chat_id=admin_id,
        text=messages.format_message("broadcast_done", total=len(users), sent=sent, failed=failed),
    )
