"""/efir command: lets a user re-enter the streams (efiry) flow at any time."""
from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.fsm.storage.base import BaseStorage
from aiogram.types import Message

import messages
from database import Database

router = Router(name="efir")


@router.message(Command("efir"))
async def cmd_efir(message: Message, db: Database, bot: Bot, storage: BaseStorage) -> None:
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if user is None:
        await message.answer(messages.format_message("start"))
        return

    from handlers.step3 import enter_step3

    await enter_step3(bot, db, storage, user_id)
