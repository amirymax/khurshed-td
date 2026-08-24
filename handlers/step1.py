"""Step 1: registration.

Flow: video1 (+ bridge reply-button) -> cover/promo (+ confirm reply-button) -> ID -> admin review.
"""
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import BaseStorage
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

import config
import keyboards
import messages
from database import Database
from states import UserStates
from utils.helpers import fsm_context, is_valid_id, send_cover_photo, send_step_video, send_submission_to_admin

router = Router(name="step1")

BRIDGE_BUTTON_TEXT_COURSE = config.MESSAGES["step1_bridge_button_course"]
BRIDGE_BUTTON_TEXT_SIGNALS = config.MESSAGES["step1_bridge_button_signals"]
CONFIRM_BUTTON_TEXT = config.MESSAGES["step1_confirm_button"]


async def enter_step1(bot: Bot, db: Database, storage: BaseStorage, user_id: int, flow: str = "course") -> None:
    """Send the step-1 lesson video with the bridge reply-button, and set FSM to step1_watching.

    `flow` is "course" (🎓 Курс button) or "signals" (📊 Сигналы button) — it picks which
    video/caption is shown here and is remembered on the user record to decide, at step2
    approval time, whether to hand out the course-group link or the эфир-group link directly.
    """
    await db.set_current_step(user_id, 1)
    await db.update_user(user_id, flow_type=flow)
    if flow == "signals":
        video_step, caption_key = 3, "step1_intro_signals"
    else:
        video_step, caption_key = 1, "step1_intro_course"
    await send_step_video(
        bot,
        user_id,
        video_step,
        reply_markup=keyboards.get_step1_bridge_reply_keyboard(flow),
        caption=messages.format_message(caption_key),
    )
    await fsm_context(bot, storage, user_id).set_state(UserStates.step1_watching)


@router.message(UserStates.step1_watching, F.text.in_({BRIDGE_BUTTON_TEXT_COURSE, BRIDGE_BUTTON_TEXT_SIGNALS}))
async def on_bridge_pressed(message: Message, state: FSMContext, bot: Bot) -> None:
    user_id = message.from_user.id
    await send_cover_photo(
        bot, user_id, config.STEP1_COVER_IMAGE, config.STEP1_COVER_VIDEO_URL, config.STEP1_COVER_SITE_URL
    )
    text = messages.format_message("step1_promo_text", site_url=config.STEP1_COVER_SITE_URL)
    await message.answer(
        text, reply_markup=keyboards.get_step1_confirm_reply_keyboard(), disable_web_page_preview=True
    )
    await state.set_state(UserStates.step1_ready)


@router.message(UserStates.step1_ready, F.text == CONFIRM_BUTTON_TEXT)
async def on_confirm_pressed(message: Message, state: FSMContext) -> None:
    await state.set_state(UserStates.step1_waiting_id)
    await message.answer(messages.format_message("step1_id_request"), reply_markup=ReplyKeyboardRemove())


@router.message(UserStates.step1_waiting_id)
async def on_id_submitted_1(message: Message, state: FSMContext, db: Database, bot: Bot) -> None:
    if not is_valid_id(message.text):
        await message.answer(messages.format_message("invalid_id_format"))
        return
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    submission_id = await db.create_submission(user_id, 1, "id", message.text.strip())
    await send_submission_to_admin(
        bot, db, step=1, user=user, submission_id=submission_id, submission_value=message.text.strip()
    )
    await state.set_state(UserStates.step1_admin_review)
    await message.answer("<b>🆔-и Шумо ба Админ Равон Карда Шуд. Интизор Шавед.</b>")


@router.message(UserStates.step1_admin_review)
async def on_message_during_review_1(message: Message) -> None:
    await message.answer(messages.format_message("id_already_under_review"))


@router.callback_query(F.data == "reverify_1")
async def on_reverify_1(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(UserStates.step1_waiting_id)
    await callback.message.answer(messages.format_message("step1_id_request"))
    await callback.answer()
