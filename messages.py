"""Text message templates and formatting helpers."""
from __future__ import annotations

import config


def format_message(key: str, **kwargs) -> str:
    """Fetch a message template from config.MESSAGES and format it with kwargs."""
    template = config.MESSAGES.get(key)
    if template is None:
        return "Неизвестная ошибка"
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template


def rejection_message(step: int, reason_key: str, amount: int | None = None) -> str:
    """Return the user-facing rejection text configured for a given step/reason.

    `amount` lets the caller pick the right top-up figure (course vs signals flow);
    defaults to config.PAYMENT_AMOUNT_USD when not given.
    """
    buttons = config.STEP_REJECTION_BUTTONS.get(step, {})
    data = buttons.get(reason_key)
    if data is None:
        return format_message("decision_not_found")
    return data["user_message"].format(amount=amount if amount is not None else config.PAYMENT_AMOUNT_USD)


def submission_notice_key(step: int) -> str:
    return {1: "step1_send_to_admin", 2: "step2_send_to_admin", 3: "step3_send_to_admin"}[step]
