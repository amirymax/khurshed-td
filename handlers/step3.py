"""Step 3: free-streams (efiry) lesson + ID submission."""
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import BaseStorage
from aiogram.types import CallbackQuery, Message

import config
import keyboards
import messages
from database import Database
from states import UserStates
from utils.helpers import fsm_context, is_valid_id, send_step_video, send_submission_to_admin

router = Router(name="step3")


async def enter_step3(bot: Bot, db: Database, storage: BaseStorage, user_id: int) -> None:
    await db.set_current_step(user_id, 3)
    await send_step_video(bot, user_id, 3)
    await bot.send_message(
        chat_id=user_id,
        text=messages.format_message("step3_video_text", amount=config.PAYMENT_AMOUNT_SIGNALS_USD),
        reply_markup=keyboards.get_watched_keyboard(3),
    )
    await fsm_context(bot, storage, user_id).set_state(UserStates.step3_watching)


@router.callback_query(F.data == "efir_yes")
async def on_efir_yes(callback: CallbackQuery, db: Database, bot: Bot, storage: BaseStorage) -> None:
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await enter_step3(bot, db, storage, callback.from_user.id)


@router.callback_query(F.data == "efir_no")
async def on_efir_no(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(messages.format_message("efir_declined"))
    await callback.answer()


@router.callback_query(F.data == "watched_3")
async def on_watched_3(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(UserStates.step3_waiting_payment_id)
    await callback.message.answer(messages.format_message("step3_id_request"))
    await callback.answer()


@router.message(UserStates.step3_waiting_payment_id)
async def on_id_submitted_3(message: Message, state: FSMContext, db: Database, bot: Bot) -> None:
    if not is_valid_id(message.text):
        await message.answer(messages.format_message("invalid_id_format"))
        return
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    submission_id = await db.create_submission(user_id, 3, "id", message.text.strip())
    await send_submission_to_admin(
        bot, db, step=3, user=user, submission_id=submission_id, submission_value=message.text.strip()
    )
    await state.set_state(UserStates.step3_admin_review)
    await message.answer("🆔-и Шумо ба Админ Равон Карда Шуд. Интизор Шавед.")


@router.message(UserStates.step3_admin_review)
async def on_message_during_review_3(message: Message) -> None:
    await message.answer(messages.format_message("id_already_under_review"))
