"""/start handling for both admins and regular users."""
import logging

from aiogram import Bot, F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.storage.base import BaseStorage
from aiogram.types import CallbackQuery, FSInputFile, Message

import config
import keyboards
import messages
from database import Database
from utils.helpers import is_admin, is_admin1, resolve_media_path

router = Router(name="start")
logger = logging.getLogger("trading_bot")


def _admin_pending_steps(user_id: int) -> list[int]:
    return [1, 2] if is_admin1(user_id) else [3]


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, db: Database) -> None:
    user_id = message.from_user.id

    if is_admin(user_id):
        pending = await db.get_pending_submissions(_admin_pending_steps(user_id))
        await message.answer(
            messages.format_message("start_admin"),
            reply_markup=keyboards.get_admin_main_menu(len(pending)),
        )
        return
    deep_link_source = command.args or "organic"
    user = await db.get_user(user_id)
    if user is None:
        await db.create_user(user_id, message.from_user.username, deep_link_source)

    text = messages.format_message("start")
    keyboard = keyboards.get_start_keyboard()
    resolved_path = resolve_media_path(config.START_IMAGE)

    if resolved_path.is_file():
        try:
            await message.answer_photo(
                FSInputFile(resolved_path), caption=text, reply_markup=keyboard
            )
            return
        except Exception:
            logger.exception("Failed to send start photo path=%s", resolved_path)
    else:
        logger.warning("Start image not found at %s; sending text without photo", resolved_path)

    await message.answer(text, reply_markup = keyboard)


@router.callback_query(F.data.in_({"start_course", "start_signals"}))
async def on_start_choice(callback: CallbackQuery, db: Database, bot: Bot, storage: BaseStorage) -> None:
    await callback.answer()
    from handlers.step1 import enter_step1

    flow = "signals" if callback.data == "start_signals" else "course"
    await enter_step1(bot, db, storage, callback.from_user.id, flow=flow)
