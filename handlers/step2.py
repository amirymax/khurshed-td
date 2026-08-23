"""Step 2: balance top-up.

Flow: cover/promo (YouTube top-up tutorial via the cover's "🎬 Видео" button) -> "Пардохт Кардам✅" -> ID -> admin review.
"""
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import BaseStorage
from aiogram.types import Message, ReplyKeyboardRemove

import config
import keyboards
import messages
from database import Database
from states import UserStates
from utils.helpers import (
    fsm_context,
    is_valid_id,
    payment_amount_for,
    send_cover_photo,
    send_submission_to_admin,
)

router = Router(name="step2")

CONFIRM_BUTTON_TEXT = config.MESSAGES["step2_confirm_button"]


async def enter_step2(bot: Bot, db: Database, storage: BaseStorage, user_id: int) -> None:
    await db.set_current_step(user_id, 2)
    await send_cover_photo(
        bot, user_id, config.STEP2_COVER_IMAGE, config.STEP2_COVER_VIDEO_URL, config.STEP2_COVER_SITE_URL
    )
    user = await db.get_user(user_id)
    amount = payment_amount_for((user or {}).get("flow_type"))
    text = messages.format_message("step2_promo_text", amount=amount)
    await bot.send_message(
        chat_id=user_id, text=text, reply_markup=keyboards.get_step2_confirm_reply_keyboard(), disable_web_page_preview=True
    )
    await fsm_context(bot, storage, user_id).set_state(UserStates.step2_watching)


@router.message(UserStates.step2_watching, F.text == CONFIRM_BUTTON_TEXT)
async def on_confirm_pressed(message: Message, state: FSMContext) -> None:
    await state.set_state(UserStates.step2_waiting_screenshot)
    await message.answer(messages.format_message("step2_id_request"), reply_markup=ReplyKeyboardRemove())


@router.message(UserStates.step2_waiting_screenshot)
async def on_id_submitted_2(message: Message, state: FSMContext, db: Database, bot: Bot) -> None:
    if not is_valid_id(message.text):
        await message.answer(messages.format_message("invalid_id_format"))
        return
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    submission_id = await db.create_submission(user_id, 2, "id", message.text.strip())
    await send_submission_to_admin(
        bot, db, step=2, user=user, submission_id=submission_id, submission_value=message.text.strip()
    )
    await state.set_state(UserStates.step2_admin_review)
    await message.answer("🆔-и Шумо ба Админ Равон Карда Шуд. Интизор Шавед.")


@router.message(UserStates.step2_admin_review)
async def on_message_during_review_2(message: Message) -> None:
    await message.answer(messages.format_message("id_already_under_review"))
