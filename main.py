"""Entry point: wires up the bot, dispatcher, database, and starts polling."""
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import config
from database import Database
from handlers import admin, broadcast, callbacks, efir, start, step1, step2, step3
from utils.helpers import setup_logging


def create_dispatcher(db: Database, storage: MemoryStorage) -> Dispatcher:
    dp = Dispatcher(storage=storage)
    dp["db"] = db
    dp["storage"] = storage

    dp.include_router(start.router)
    dp.include_router(step1.router)
    dp.include_router(step2.router)
    dp.include_router(step3.router)
    dp.include_router(admin.router)
    dp.include_router(broadcast.router)
    dp.include_router(callbacks.router)
    dp.include_router(efir.router)

    return dp


async def main() -> None:
    logger = setup_logging()

    db = Database(config.DATABASE_PATH)
    await db.connect()

    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = MemoryStorage()
    dp = create_dispatcher(db, storage)

    logger.info("Bot starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        logger.info("Bot stopping...")
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
