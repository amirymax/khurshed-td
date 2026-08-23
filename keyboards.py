"""All inline and reply keyboards used by the bot."""
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

import config

# ============================= USER KEYBOARDS =============================

_WATCHED_TEXT = {
    1: "✅ Ман регистрацияро гузаштам",
    2: "✅ Ман пополнить кардам",
    3: "✅ Ман пополнить кардам",
}


def get_start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎓 Курс", callback_data="start_course", style='success'),
                InlineKeyboardButton(text="📊 Сигналы", callback_data="start_signals", style='primary'),
            ]
        ]
    )


def get_watched_keyboard(step: int) -> InlineKeyboardMarkup:
    text = _WATCHED_TEXT.get(step, config.BUTTONS["watched"])
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=f"watched_{step}")]]
    )


def get_paid_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=config.BUTTONS["paid"], callback_data="paid")]
        ]
    )


def get_efir_question_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Бале", callback_data="efir_yes"),
                InlineKeyboardButton(text="❌ Не", callback_data="efir_no"),
            ]
        ]
    )


def get_reverify_keyboard(step: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Верификацияро гузаштам", callback_data=f"reverify_{step}")]
        ]
    )


def get_cover_keyboard(video_url: str, site_url: str) -> InlineKeyboardMarkup:
    """Inline URL buttons attached to a promo "cover" image."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎬 Видео", url=video_url),
                InlineKeyboardButton(text="📊 Сайт", url=site_url),
            ]
        ]
    )


def get_step1_bridge_reply_keyboard(flow: str = "course") -> ReplyKeyboardMarkup:
    key = "step1_bridge_button_signals" if flow == "signals" else "step1_bridge_button_course"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=config.MESSAGES[key])]],
        resize_keyboard=True,
    )


def get_step1_confirm_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=config.MESSAGES["step1_confirm_button"], style='success')]],
        resize_keyboard=True,
    )


def get_step2_confirm_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=config.MESSAGES["step2_confirm_button"])]],
        resize_keyboard=True,
    )


# ============================= ADMIN KEYBOARDS =============================


def get_admin_main_menu(pending_count: int = 0) -> InlineKeyboardMarkup:
    queue_label = f"👥 Очередь заявок ({pending_count} новых)" if pending_count else "👥 Очередь заявок"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text=queue_label, callback_data="admin_queue")],
            [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="⚙️ Управление", callback_data="admin_manage")],
        ]
    )


def get_broadcast_prompt_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Отменить", callback_data="broadcast_cancel")]]
    )


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить всем", callback_data="broadcast_confirm"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="broadcast_cancel"),
            ]
        ]
    )


def get_admin_stats_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ В меню", callback_data="admin_menu")]]
    )


def get_admin_queue_pagination_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    total_pages = max(total_pages, 1)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="◀️ Пред", callback_data="admin_queue_prev"),
                InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="noop"),
                InlineKeyboardButton(text="Далее ➡️", callback_data="admin_queue_next"),
            ],
            [InlineKeyboardButton(text="↩️ В меню", callback_data="admin_menu")],
        ]
    )


APPROVE_BUTTON_TEXT = "✅ Қабул кардан"
ALREADY_BUTTON_TEXT = "👤 Дар группа иштирок дорад"


def _build_step_decision_keyboard(step: int, submission_id: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for reason_key, reason_data in config.STEP_REJECTION_BUTTONS[step].items():
        rows.append(
            [
                InlineKeyboardButton(
                    text=reason_data["text"],
                    callback_data=f"admin_step{step}_reject_{submission_id}_{reason_key}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=APPROVE_BUTTON_TEXT,
                callback_data=f"admin_step{step}_approve_{submission_id}",
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text=ALREADY_BUTTON_TEXT,
                callback_data=f"admin_step{step}_already_{submission_id}",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_step1_decision_keyboard(submission_id: int) -> InlineKeyboardMarkup:
    return _build_step_decision_keyboard(1, submission_id)


def get_admin_step2_decision_keyboard(submission_id: int) -> InlineKeyboardMarkup:
    return _build_step_decision_keyboard(2, submission_id)


def get_admin_step3_decision_keyboard(submission_id: int) -> InlineKeyboardMarkup:
    return _build_step_decision_keyboard(3, submission_id)


def get_admin_decision_keyboard(step: int, submission_id: int) -> InlineKeyboardMarkup:
    return _build_step_decision_keyboard(step, submission_id)


def get_admin_manage_menu(is_admin1: bool, is_admin2: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if is_admin1:
        rows.append([InlineKeyboardButton(text="✏️ Редактировать кнопки Шага 1", callback_data="admin_edit_step1")])
        rows.append([InlineKeyboardButton(text="✏️ Редактировать кнопки Шага 2", callback_data="admin_edit_step2")])
    if is_admin2:
        rows.append([InlineKeyboardButton(text="✏️ Редактировать кнопки Шага 3", callback_data="admin_edit_step3")])
    rows.append([InlineKeyboardButton(text="🔗 Список deep-links", callback_data="admin_deeplinks")])
    rows.append([InlineKeyboardButton(text="📝 Просмотр лога", callback_data="admin_logs")])
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
