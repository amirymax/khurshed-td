"""Loads all bot configuration from environment variables (.env)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _get_int(name: str, default: int | None = None) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        if default is not None:
            return default
        raise ValueError(f"Missing required environment variable: {name}")
    return int(value)


def _get_str(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


BOT_TOKEN: str = _get_str("BOT_TOKEN")

ADMIN1_ID: int = _get_int("ADMIN1_ID")
ADMIN2_ID: int = _get_int("ADMIN2_ID")
ADMIN_IDS: list[int] = [ADMIN1_ID, ADMIN2_ID]

TARGET_GROUP1_ID: int = _get_int("TARGET_GROUP1_ID")
TARGET_GROUP2_ID: int = _get_int("TARGET_GROUP2_ID")
SOURCE_GROUP_ID: int = _get_int("SOURCE_GROUP_ID")

VIDEO_MESSAGE_IDS: dict[str, int] = {
    "step1": _get_int("VIDEO_MESSAGE_ID_STEP1"),
    "step3": _get_int("VIDEO_MESSAGE_ID_STEP3"),
}

PAYMENT_AMOUNT_USD: int = _get_int("PAYMENT_AMOUNT_USD", 50)

# Top-up amount depends on the flow: course-group access vs direct эфир (signals) access.
PAYMENT_AMOUNT_COURSE_USD: int = _get_int("PAYMENT_AMOUNT_COURSE_USD", 50)
PAYMENT_AMOUNT_SIGNALS_USD: int = _get_int("PAYMENT_AMOUNT_SIGNALS_USD", 100)

DATABASE_PATH: str = _get_str("DATABASE_PATH", "users.db")

BOT_USERNAME: str = _get_str("BOT_USERNAME", "your_bot")

INVITE_LINK_EXPIRE_SECONDS: int = _get_int("INVITE_LINK_EXPIRE_SECONDS", 604800)

LOG_LEVEL: str = _get_str("LOG_LEVEL", "INFO")
LOG_FILE: str = _get_str("LOG_FILE", "logs/bot.log")

# === Promo "cover" images shown after the bridge/confirm reply-buttons ===
# Local file paths (relative to the project root); drop the actual images here.
STEP1_COVER_IMAGE: str = _get_str("STEP1_COVER_IMAGE", "media/step1_cover.jpg")
STEP2_COVER_IMAGE: str = _get_str("STEP2_COVER_IMAGE", "media/step2_cover.jpg")

# === /start photo (local file path, relative to the project root) ===
START_IMAGE: str = _get_str("START_IMAGE", "media/start.jpg")

# === Inline URL buttons attached to each cover image ===
STEP1_COVER_VIDEO_URL: str = _get_str("STEP1_COVER_VIDEO_URL", "https://example.com/TODO_SET_STEP1_VIDEO_LINK")
STEP1_COVER_SITE_URL: str = _get_str("STEP1_COVER_SITE_URL", "https://broker-qx.pro/sign-up/?lid=256965")
STEP2_COVER_VIDEO_URL: str = _get_str("STEP2_COVER_VIDEO_URL", "https://example.com/TODO_SET_STEP2_VIDEO_LINK")
STEP2_COVER_SITE_URL: str = _get_str("STEP2_COVER_SITE_URL", "https://broker-qx.pro/sign-up/?lid=256965")

# === Admin broadcast (mailing) ===
# Pause between messages while broadcasting, to stay under Telegram's rate limits.
BROADCAST_DELAY_SECONDS: float = _get_float("BROADCAST_DELAY_SECONDS", 0.05)

MESSAGES: dict[str, str] = {
    "start": "<b>👇🏻Маълумоти Пурра:</b>",
    "start_admin": "👑 Панель администратора",

    "step1_intro_course": "<b>👆Маълумоти Пурра:\n\n🎓Курс</b>",
    "step1_intro_signals": "<b>👆Маълумоти Пурра:\n\n📊Сигналы</b>",
    "step1_bridge_button_course": "🎓 Мехоҳам Дар Курс Иштирок Кунам",
    "step1_bridge_button_signals": "📊 Мехоҳам Дар Эфир Иштирок Кунам",
    "step1_promo_text": (
        "👆👆👆👆👆\n\n"
        "<b>🎬 Видиёро Тамошо Карда</b> \n\n"
        "<b>❗️Бе Мушкили Регистрация Кунед</b> ✅\n\n"
        "<b>🔗 Ссылкаи Сайт</b> 📊\n"
        "👇👇👇👇👇👇👇\n\n"
        "{site_url}"
    ),
    "step1_confirm_button": "Maн Рeгистрaцияро Гузаштам✅",
    "step1_id_request": "<b>🆔 - Рақами</b> Худро Равон Кунед",
    "step1_send_to_admin": "🆕 Новая заявка — Шаг 1 (регистрация)\n👤 @{username}\n📝 Отправлено: {submission_value}",
    "step1_not_verified": "<b>Аккаунти Шумо Верификация нашудааст.\nАз Верификация Гузашта, Кнопкаи Поёнро Пахш Кунед.</b>",
    "step1_approved": "<b>Шумо Аз Верификация Гузаштед✅\n\nМетавонед Ба Дарси 2 Гузаред🎓</b>",
    "step1_already_in_group": "<b>Шумо Аллакай Дар Курс Иштирок Доред✅\n\nМехоҳед ба Гурӯҳи Эфир Дохил Шавед?</b>",

    "step2_promo_text": (
        "<b>Барои Ба Группа Дохил Шудан</b> ❗️\n\n"
        "<b>Дар Сайтатон {amount}$ Пополнить Кунед </b>✅\n\n"
        "<b>Пополнить Кардан Дар Сайт</b>📊\n"
    ),
    "step2_confirm_button": "Пардохт Кардам✅",
    "step2_id_request": "<b>🆔 - Рақами</b> Худро Равон Кунед",
    "step2_send_to_admin": "🆕 Новая заявка — Шаг 2 (пополнение)\n👤 @{username}\n📝 Отправлено: {submission_value}",
    "step2_approved": (
        "<b>Шумо Ба Курс Қабул Шудед✅\n\nМарҳамат Ба Гурупаи Курс🎓\n\nБа Ссылка Як Бор Даромада Мешавад Даромадед Подписаться Кунед!</b>\n\n👇👇👇👇\n{invite_link}"
    ),
    "step2_approved_signals": (
        "<b>Шумо Ба Гурӯҳи Эфир Қабул Шудед✅\n\nМарҳамат Ба Гурӯҳи Эфир📊\n\nБа Ссылка Як Бор Даромада Мешавад Даромадед Подписаться Кунед!</b>\n\n"
        "👇👇👇👇\n{invite_link}"
    ),
    "step2_not_replenished": "<b>Баланси Шумо Пур Нашудааст. Балансро Ба Андозаи {amount}$ Пур Карда, 🆔-ро Равон Кунед.</b>",
    "step2_not_verified": "<b>Баланси Шумо Пур Нашудааст. Балансро Ба Андозаи {amount}$ Пур Карда, 🆔-ро Равон Кунед.</b>",

    "step3_video_text": "Барои иштирок дар Эфири Бепул балансро ${amount}. пополнить кунед.",
    "step3_id_request": "🆔 - и Худро равон кунед",
    "step3_send_to_admin": "🆕 Новая заявка — Шаг 3 (эфиры)\n👤 @{username}\n📝 Отправлено: {submission_value}",
    "step3_approved": "<b>Шумо Ба Гурӯҳи Эфир Қабул Шудед✅\n\nМарҳамат Ба Гурӯҳи Эфир📊\n\nБа Ссылка Як Бор Даромада Мешавад Даромадед Подписаться Кунед!</b>\n\n👇👇👇👇\n{invite_link}",
    "step3_not_verified": "<b>Баланси Шумо Пур Нашудааст. Балансро Ба Андозаи {amount}$ Пур Карда, 🆔-ро Равон Кунед.</b>",
    "step3_insufficient_balance": "<b>Баланси Шумо Пур Нашудааст. Балансро Ба Андозаи {amount}$ Пур Карда, 🆔-ро Равон Кунед.</b>",
    "step3_already_in_group": "<b>Шумо Аллакай Дар Эфир Иштирок Доред✅</b>",

    "other_link_rejection": "<b>🆔 - и Шумо ба Ссылкаи Мо Нест\nУдалить Аккаунт карда, Ба ссылкаи Мо Регистрация кунед</b>\n\n /start - ро пахш кунед.",
    "other_link_rejection_step2": "<b>🆔 - и Шумо ба Ссылкаи Мо Нест\nУдалить Аккаунт карда, Ба ссылкаи Мо Регистрация кунед</b>\n\n /start - ро пахш кунед.",
    "other_link_rejection_step3": "<b>🆔 - и Шумо ба Ссылкаи Мо Нест\nУдалить Аккаунт карда, Ба ссылкаи Мо Регистрация кунед</b>\n\n /start - ро пахш кунед.",

    "efir_question": "<b>Мехоҳед ба Гурӯҳи Эфир Дохил Шавед?</b>",
    "efir_declined": "Хуб! Агар ба эфир дохил шудан хоҳед, ин командаро равон кунед:\n\n /efir",

    "invite_error": "Не удалось создать пригласительную ссылку. Пожалуйста, обратитесь к администратору.",
    "decision_not_found": "Заявка не найдена или уже обработана.",
    "not_admin": "У вас нет доступа к этой команде.",

    "invalid_id_format": "<b>🆔 - и ҳақиқиро равон кунед</b>",
    "id_already_under_review": "<b>🆔 - и шумо санҷида шуда истодааст</b>",

    "broadcast_prompt": (
        "Отправьте сообщение для рассылки — текст (с форматированием), фото/видео с подписью, "
        "голосовое, видео-кружок и т.д. Оно будет разослано всем пользователям как есть."
    ),
    "broadcast_preview_prompt": "👆 Так будет выглядеть рассылка. Отправить всем пользователям?",
    "broadcast_cancelled": "Рассылка отменена.",
    "broadcast_started": "🚀 Рассылка запущена, это может занять некоторое время...",
    "broadcast_done": "✅ Рассылка завершена.\n👥 Всего пользователей: {total}\n📤 Успешно: {sent}\n❌ Не удалось: {failed}",
}

BUTTONS: dict[str, str] = {
    "watched": "✅ Тамошо кардам",
    "paid": "💳 Пардохт кардам",
}

STEP1_REJECTION_BUTTONS: dict[str, dict[str, str]] = {
    "other_link": {
        "text": "🔗 Ба ссылкаи мо нест",
        "user_message": MESSAGES["other_link_rejection"],
    },
    "not_verified": {
        "text": "❌ Верификация нашудааст",
        "user_message": MESSAGES["step1_not_verified"],
    },
}

STEP2_REJECTION_BUTTONS: dict[str, dict[str, str]] = {
    "other_link": {
        "text": "🔗 Ба ссылкаи мо нест",
        "user_message": MESSAGES["other_link_rejection_step2"],
    },
    "not_verified": {
        "text": "❌ Верификация нашудааст",
        "user_message": MESSAGES["step2_not_verified"],
    },
    "not_replenished": {
        "text": "💰 Баланс пополнить нашудааст",
        "user_message": MESSAGES["step2_not_replenished"],
    },
}

STEP3_REJECTION_BUTTONS: dict[str, dict[str, str]] = {
    "other_link": {
        "text": "🔗 Ба ссылкаи мо нест",
        "user_message": MESSAGES["other_link_rejection_step3"],
    },
    "not_verified": {
        "text": "❌ Верификация нашудааст",
        "user_message": MESSAGES["step3_not_verified"],
    },
    "insufficient_balance": {
        "text": "⚠️ Пополнить накардааст",
        "user_message": MESSAGES["step3_insufficient_balance"],
    },
}

STEP_REJECTION_BUTTONS: dict[int, dict[str, dict[str, str]]] = {
    1: STEP1_REJECTION_BUTTONS,
    2: STEP2_REJECTION_BUTTONS,
    3: STEP3_REJECTION_BUTTONS,
}

STEP_ADMIN: dict[int, int] = {
    1: ADMIN1_ID,
    2: ADMIN1_ID,
    3: ADMIN2_ID,
}

QUEUE_PAGE_SIZE = 5
