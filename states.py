"""FSM states used across the bot."""
from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    step1_watching = State()        # waiting for the "Мехоҳам..." bridge reply-button
    step1_ready = State()           # cover/promo shown, waiting for the registration confirm reply-button
    step1_waiting_id = State()
    step1_admin_review = State()

    step2_watching = State()        # cover/promo shown, waiting for the payment confirm reply-button
    step2_waiting_screenshot = State()
    step2_admin_review = State()

    step3_watching = State()
    step3_waiting_payment_id = State()
    step3_admin_review = State()


class AdminStates(StatesGroup):
    reviewing_submission = State()
    broadcast_waiting_content = State()  # waiting for the admin to send the message to broadcast
    broadcast_confirm = State()          # content received, waiting for send/cancel confirmation
