"""Miscellaneous helper functions: invite links, video copying, admin notifications, logging."""
from __future__ import annotations

import html
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.types import FSInputFile

import config
import keyboards
import messages
from database import Database

logger = logging.getLogger("trading_bot")


def setup_logging() -> logging.Logger:
    """Configure the root bot logger to write to config.LOG_FILE and stdout."""
    os.makedirs(os.path.dirname(config.LOG_FILE) or ".", exist_ok=True)
    logger.setLevel(config.LOG_LEVEL)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = logging.FileHandler(config.LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


def is_admin1(user_id: int) -> bool:
    return user_id == config.ADMIN1_ID


def is_admin2(user_id: int) -> bool:
    return user_id == config.ADMIN2_ID


ID_PATTERN = re.compile(r"^\d{8,9}$")


def is_valid_id(text: str | None) -> bool:
    """A Telegram/broker ID is exactly 8 or 9 digits, nothing else."""
    return bool(text) and bool(ID_PATTERN.fullmatch(text.strip()))


def payment_amount_for(flow_type: str | None) -> int:
    """Top-up amount for a user's flow: 100$ for signals (эфир), 50$ for course."""
    return config.PAYMENT_AMOUNT_SIGNALS_USD if flow_type == "signals" else config.PAYMENT_AMOUNT_COURSE_USD


def admin_for_step(step: int, flow_type: str | None) -> int:
    """Which admin reviews a submission at this step, given the user's flow.

    Course-flow users: ADMIN1 reviews steps 1-2, ADMIN2 reviews step 3 (opt-in эфир).
    Signals-flow users go through steps 1-2 too, but that whole flow IS the эфир
    signup, so ADMIN2 reviews both of their steps instead of ADMIN1.
    """
    if flow_type == "signals" and step in (1, 2):
        return config.ADMIN2_ID
    return config.STEP_ADMIN[step]


def submissions_for_admin(submissions: list[dict], admin_id: int) -> list[dict]:
    """Filter a list of submissions (as returned by Database.get_pending_submissions,
    which includes each row's `flow_type`) down to the ones this admin is responsible for."""
    return [s for s in submissions if admin_for_step(s["step"], s.get("flow_type")) == admin_id]


def display_name(user: dict) -> str:
    username = user.get("username")
    return f"@{username}" if username else f"ID:{user['user_id']}"


def fsm_context(bot: Bot, storage: BaseStorage, user_id: int) -> FSMContext:
    """Build an FSMContext for a user's private chat, independent of the current update.

    Needed when an admin's decision (made in the admin's own chat) must change the
    FSM state of the *submitting* user, who is not part of the current update.
    """
    key = StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id)
    return FSMContext(storage=storage, key=key)


async def send_step_video(bot: Bot, chat_id: int, step: int, reply_markup=None, caption: str | None = None):
    """Copy the pre-uploaded lesson video for `step` from SOURCE_GROUP_ID to chat_id."""
    message_id = config.VIDEO_MESSAGE_IDS[f"step{step}"]
    kwargs = dict(chat_id=chat_id, from_chat_id=config.SOURCE_GROUP_ID, message_id=message_id)
    if reply_markup is not None:
        kwargs["reply_markup"] = reply_markup
    if caption is not None:
        kwargs["caption"] = caption
    try:
        return await bot.copy_message(**kwargs)
    except Exception:
        logger.exception("Failed to copy step%s video to chat_id=%s", step, chat_id)
        return None


def resolve_media_path(path_str: str) -> Path:
    path = Path(path_str)
    return path if path.is_absolute() else (config.BASE_DIR / path)


async def send_cover_photo(bot: Bot, chat_id: int, image_path: str, video_url: str, site_url: str):
    """Send a promo "cover" image with 🎬 Видео / 📊 Сайт inline URL buttons.

    Falls back to a text-only message with the same buttons if the image file
    hasn't been added to the project yet (see config.STEP1_COVER_IMAGE / STEP2_COVER_IMAGE).
    """
    keyboard = keyboards.get_cover_keyboard(video_url, site_url)
    resolved_path = resolve_media_path(image_path)

    if resolved_path.is_file():
        try:
            return await bot.send_photo(
                chat_id=chat_id, photo=FSInputFile(resolved_path), reply_markup=keyboard
            )
        except Exception:
            logger.exception("Failed to send cover photo chat_id=%s path=%s", chat_id, resolved_path)
    else:
        logger.warning("Cover image not found at %s; sending buttons without photo", resolved_path)

    return await bot.send_message(chat_id=chat_id, text="🖼 Обложка", reply_markup=keyboard)


async def create_unique_invite_link(bot: Bot, db: Database, group_id: int, user_id: int) -> str | None:
    """Create a one-time (member_limit=1) invite link for group_id and persist it."""
    expire_date = None
    if config.INVITE_LINK_EXPIRE_SECONDS:
        expire_date = datetime.now(timezone.utc) + timedelta(
            seconds=config.INVITE_LINK_EXPIRE_SECONDS
        )
    try:
        invite = await bot.create_chat_invite_link(
            chat_id=group_id,
            member_limit=1,
            expire_date=expire_date,
        )
    except Exception:
        logger.exception("Failed to create invite link for group_id=%s user_id=%s", group_id, user_id)
        return None

    await db.add_invite(
        user_id=user_id,
        group_id=group_id,
        invite_link=invite.invite_link,
        expires_at=expire_date.isoformat() if expire_date else None,
    )
    return invite.invite_link


async def notify_admin(bot: Bot, admin_id: int, text: str, reply_markup=None) -> bool:
    try:
        await bot.send_message(chat_id=admin_id, text=text, reply_markup=reply_markup)
        return True
    except Exception:
        logger.exception("Failed to notify admin_id=%s", admin_id)
        return False


async def send_submission_to_admin(
    bot: Bot,
    db: Database,
    step: int,
    user: dict,
    submission_id: int,
    submission_value: str,
) -> bool:
    """Format and send a new submission notification to the admin responsible for `step`."""
    admin_id = admin_for_step(step, user.get("flow_type"))
    text = messages.format_message(
        messages.submission_notice_key(step),
        username=html.escape(user.get("username") or "нет username"),
        user_id=user["user_id"],
        submission_value=html.escape(submission_value or ""),
    )
    keyboard = keyboards.get_admin_decision_keyboard(step, submission_id)
    sent = await notify_admin(bot, admin_id, text, keyboard)
    logger.info(
        "submission #%s step=%s user_id=%s sent_to_admin=%s (admin_id=%s)",
        submission_id, step, user["user_id"], sent, admin_id,
    )
    return sent
