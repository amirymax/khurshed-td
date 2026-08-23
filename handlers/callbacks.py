"""Admin decision callbacks: approve / reject / already-in-group for all three steps."""
import re

from aiogram import Bot, Router
from aiogram.fsm.storage.base import BaseStorage
from aiogram.types import CallbackQuery

import config
import keyboards
import messages
from database import Database
from utils.helpers import create_unique_invite_link, fsm_context, payment_amount_for

router = Router(name="callbacks")

APPROVE_RE = re.compile(r"^admin_step(?P<step>[123])_approve_(?P<sub_id>\d+)$")
REJECT_RE = re.compile(r"^admin_step(?P<step>[123])_reject_(?P<sub_id>\d+)_(?P<reason>\w+)$")
ALREADY_RE = re.compile(r"^admin_step(?P<step>[123])_already_(?P<sub_id>\d+)$")


def _is_approve(callback: CallbackQuery) -> bool:
    return bool(APPROVE_RE.match(callback.data or ""))


def _is_reject(callback: CallbackQuery) -> bool:
    return bool(REJECT_RE.match(callback.data or ""))


def _is_already(callback: CallbackQuery) -> bool:
    return bool(ALREADY_RE.match(callback.data or ""))


def _admin_allowed(user_id: int, step: int) -> bool:
    return user_id == config.STEP_ADMIN[step]


async def _mark_decided(callback: CallbackQuery, decision_label: str) -> None:
    """Edit the admin's notification in place: strip the buttons and append which
    decision was made, so the admin can see at a glance who was approved/rejected."""
    original = callback.message.html_text or callback.message.text or ""
    try:
        await callback.message.edit_text(f"{original}\n\n{decision_label}", reply_markup=None)
    except Exception:
        await callback.message.edit_reply_markup(reply_markup=None)


@router.callback_query(_is_approve)
async def on_admin_approve(callback: CallbackQuery, db: Database, bot: Bot, storage: BaseStorage) -> None:
    match = APPROVE_RE.match(callback.data)
    step = int(match["step"])
    submission_id = int(match["sub_id"])
    admin_id = callback.from_user.id

    if not _admin_allowed(admin_id, step):
        await callback.answer(messages.format_message("not_admin"), show_alert=True)
        return

    submission = await db.get_submission(submission_id)
    if submission is None or submission["admin_decision"] != "pending":
        await callback.answer(messages.format_message("decision_not_found"), show_alert=True)
        return

    await db.decide_submission(submission_id, "approved", admin_id=admin_id)
    target_user_id = submission["user_id"]

    await callback.answer("Одобрено ✅")
    await _mark_decided(callback, keyboards.APPROVE_BUTTON_TEXT)

    if step == 1:
        await db.set_current_step(target_user_id, 2)
        await bot.send_message(chat_id=target_user_id, text=messages.format_message("step1_approved"))
        from handlers.step2 import enter_step2

        await enter_step2(bot, db, storage, target_user_id)

    elif step == 2:
        target_user = await db.get_user(target_user_id)
        is_signals = (target_user or {}).get("flow_type") == "signals"

        if is_signals:
            # "Сигналы" IS the эфир group — top-up approval goes straight to the эфир invite link.
            invite_link = await create_unique_invite_link(
                bot, db, config.TARGET_GROUP2_ID, target_user_id
            )
            await db.set_group_status(target_user_id, 2, "joined")
            await db.set_current_step(target_user_id, 4)
            await db.update_user(target_user_id, status="completed")
            if invite_link:
                await bot.send_message(
                    chat_id=target_user_id,
                    text=messages.format_message("step2_approved_signals", invite_link=invite_link),
                )
            else:
                await bot.send_message(chat_id=target_user_id, text=messages.format_message("invite_error"))
        else:
            await db.set_current_step(target_user_id, 3)
            invite_link = await create_unique_invite_link(
                bot, db, config.TARGET_GROUP1_ID, target_user_id
            )
            await db.set_group_status(target_user_id, 1, "joined")
            if invite_link:
                await bot.send_message(
                    chat_id=target_user_id,
                    text=messages.format_message("step2_approved", invite_link=invite_link),
                )
            else:
                await bot.send_message(chat_id=target_user_id, text=messages.format_message("invite_error"))
            await bot.send_message(
                chat_id=target_user_id,
                text=messages.format_message("efir_question"),
                reply_markup=keyboards.get_efir_question_keyboard(),
            )
        await fsm_context(bot, storage, target_user_id).clear()

    elif step == 3:
        invite_link = await create_unique_invite_link(
            bot, db, config.TARGET_GROUP2_ID, target_user_id
        )
        await db.set_group_status(target_user_id, 2, "joined")
        await db.set_current_step(target_user_id, 4)
        await db.update_user(target_user_id, status="completed")
        if invite_link:
            await bot.send_message(
                chat_id=target_user_id,
                text=messages.format_message("step3_approved", invite_link=invite_link),
            )
        else:
            await bot.send_message(chat_id=target_user_id, text=messages.format_message("invite_error"))
        await fsm_context(bot, storage, target_user_id).clear()


@router.callback_query(_is_reject)
async def on_admin_reject(callback: CallbackQuery, db: Database, bot: Bot, storage: BaseStorage) -> None:
    match = REJECT_RE.match(callback.data)
    step = int(match["step"])
    submission_id = int(match["sub_id"])
    reason = match["reason"]
    admin_id = callback.from_user.id

    if not _admin_allowed(admin_id, step):
        await callback.answer(messages.format_message("not_admin"), show_alert=True)
        return

    submission = await db.get_submission(submission_id)
    if submission is None or submission["admin_decision"] != "pending":
        await callback.answer(messages.format_message("decision_not_found"), show_alert=True)
        return

    await db.decide_submission(submission_id, "rejected", admin_id=admin_id, rejection_reason=reason)
    target_user_id = submission["user_id"]

    await callback.answer("Отклонено ❌")
    reason_label = config.STEP_REJECTION_BUTTONS[step][reason]["text"]
    await _mark_decided(callback, reason_label)

    amount = None
    if step == 2:
        target_user = await db.get_user(target_user_id)
        amount = payment_amount_for((target_user or {}).get("flow_type"))
    elif step == 3:
        amount = config.PAYMENT_AMOUNT_SIGNALS_USD
    text = messages.rejection_message(step, reason, amount=amount)
    reply_markup = keyboards.get_reverify_keyboard(1) if (step == 1 and reason == "not_verified") else None
    await bot.send_message(chat_id=target_user_id, text=text, reply_markup=reply_markup)

    from states import UserStates

    waiting_state = {2: UserStates.step2_waiting_screenshot, 3: UserStates.step3_waiting_payment_id}.get(step)
    if waiting_state is not None:
        await fsm_context(bot, storage, target_user_id).set_state(waiting_state)


@router.callback_query(_is_already)
async def on_admin_already(callback: CallbackQuery, db: Database, bot: Bot, storage: BaseStorage) -> None:
    match = ALREADY_RE.match(callback.data)
    step = int(match["step"])
    submission_id = int(match["sub_id"])
    admin_id = callback.from_user.id

    if not _admin_allowed(admin_id, step):
        await callback.answer(messages.format_message("not_admin"), show_alert=True)
        return

    submission = await db.get_submission(submission_id)
    if submission is None:
        await callback.answer(messages.format_message("decision_not_found"), show_alert=True)
        return

    if submission["admin_decision"] == "pending":
        await db.decide_submission(
            submission_id, "approved", admin_id=admin_id, rejection_reason="already_in_group"
        )
    target_user_id = submission["user_id"]

    await callback.answer()
    await _mark_decided(callback, keyboards.ALREADY_BUTTON_TEXT)

    if step in (1, 2):
        await db.set_group_status(target_user_id, 1, "joined")
        await bot.send_message(
            chat_id=target_user_id,
            text=messages.format_message("step1_already_in_group"),
            reply_markup=keyboards.get_efir_question_keyboard(),
        )
        await fsm_context(bot, storage, target_user_id).clear()

    elif step == 3:
        await db.set_group_status(target_user_id, 2, "joined")
        await bot.send_message(chat_id=target_user_id, text=messages.format_message("step3_already_in_group"))
        await fsm_context(bot, storage, target_user_id).clear()
