"""Admin panel: statistics, submission queue (paginated), management menu."""
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

import config
import keyboards
from database import Database
from utils.analytics import AnalyticsManager
from utils.helpers import is_admin, is_admin1, is_admin2

router = Router(name="admin")

ADMIN_QUEUE_PAGE_KEY = "admin_queue_page"


def admin_steps(user_id: int) -> list[int]:
    return [1, 2] if is_admin1(user_id) else [3]


@router.callback_query(F.data == "admin_menu")
async def admin_menu(callback: CallbackQuery, db: Database) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return
    pending = await db.get_pending_submissions(admin_steps(callback.from_user.id))
    await callback.message.edit_text(
        "👑 Панель администратора", reply_markup=keyboards.get_admin_main_menu(len(pending))
    )
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery, db: Database) -> None:
    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer()
        return

    analytics = AnalyticsManager(db)
    general = await analytics.get_general_stats()
    deeplink = await analytics.get_deeplink_stats()
    weekly = await analytics.get_weekly_deeplink_stats()
    distribution = await analytics.get_step_distribution()

    lines = [
        f"📊 Общее кол-во стартов: {general['total_starts']}",
        f"За неделю: {general['starts_this_week']}",
        "",
    ]

    if is_admin1(user_id):
        lines.append(f"Шаг 1 (регистрация): {distribution['step1']['total']}")
        lines.append(f"Шаг 2 (пополнение): {distribution['step2']['total']}")
        lines.append(f"Завершили курс: {general['by_step']['step3']}")
    if is_admin2(user_id):
        lines.append(f"Шаг 3 (эфиры): {distribution['step3']['total']}")
        lines.append(f"Завершили эфиры: {general['completed']}")

    lines.append("")
    lines.append("Deep-link → всего → за неделю")
    for source in sorted(set(deeplink) | set(weekly)):
        lines.append(f"{source}: {deeplink.get(source, 0)} / {weekly.get(source, 0)}")

    lines.append("")
    lines.append(f"% завершения: {general['completion_rate']}%")

    await callback.message.edit_text("\n".join(lines), reply_markup=keyboards.get_admin_stats_back_keyboard())
    await callback.answer()


async def _paginate_queue(db: Database, state: FSMContext, admin_user_id: int, page: int):
    submissions = await db.get_pending_submissions(admin_steps(admin_user_id))
    page_size = config.QUEUE_PAGE_SIZE
    total_pages = max((len(submissions) + page_size - 1) // page_size, 1)
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    chunk = submissions[start : start + page_size]
    await state.update_data(**{ADMIN_QUEUE_PAGE_KEY: page})
    return chunk, page, total_pages


@router.callback_query(F.data.in_({"admin_queue", "admin_queue_prev", "admin_queue_next"}))
async def admin_queue(callback: CallbackQuery, db: Database, state: FSMContext, bot: Bot) -> None:
    admin_user_id = callback.from_user.id
    if not is_admin(admin_user_id):
        await callback.answer()
        return

    data = await state.get_data()
    page = data.get(ADMIN_QUEUE_PAGE_KEY, 1)
    if callback.data == "admin_queue_prev":
        page -= 1
    elif callback.data == "admin_queue_next":
        page += 1
    elif callback.data == "admin_queue":
        page = 1

    chunk, page, total_pages = await _paginate_queue(db, state, admin_user_id, page)
    await callback.answer()

    if not chunk:
        await bot.send_message(
            chat_id=admin_user_id,
            text="Нет заявок в очереди.",
            reply_markup=keyboards.get_admin_stats_back_keyboard(),
        )
        return

    for sub in chunk:
        text = (
            f"👤 User: @{sub['username'] or '—'}\n"
            f"📍 Шаг: {sub['step']}\n"
            f"📝 Заявка: {sub['submission_value']}"
        )
        await bot.send_message(
            chat_id=admin_user_id,
            text=text,
            reply_markup=keyboards.get_admin_decision_keyboard(sub["step"], sub["id"]),
        )

    await bot.send_message(
        chat_id=admin_user_id,
        text=f"📄 Страница {page}/{total_pages}",
        reply_markup=keyboards.get_admin_queue_pagination_keyboard(page, total_pages),
    )


@router.callback_query(F.data == "admin_manage")
async def admin_manage(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer()
        return
    keyboard = keyboards.get_admin_manage_menu(is_admin1(user_id), is_admin2(user_id))
    await callback.message.edit_text("⚙️ Управление", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.in_({"admin_edit_step1", "admin_edit_step2", "admin_edit_step3", "admin_deeplinks", "admin_logs"}))
async def admin_manage_stub(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.answer("Раздел в разработке", show_alert=True)


@router.callback_query(F.data == "noop")
async def admin_noop(callback: CallbackQuery) -> None:
    await callback.answer()
