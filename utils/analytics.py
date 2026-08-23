"""Statistics and analytics aggregation over the bot's database."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from database import Database

STEPS = (1, 2, 3)


class AnalyticsManager:
    """Computes aggregated statistics from the Database."""

    def __init__(self, db: Database):
        self.db = db

    @staticmethod
    def _week_ago_iso() -> str:
        return (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    async def get_general_stats(self) -> dict:
        total_starts = await self.db.count_users()
        starts_this_week = await self.db.count_users_since(self._week_ago_iso())
        completed = await self.db.count_completed_users()
        by_step = {f"step{step}": await self.db.count_users_by_step(step) for step in STEPS}
        completion_rate = (completed / total_starts * 100) if total_starts else 0.0

        return {
            "total_starts": total_starts,
            "starts_this_week": starts_this_week,
            "completed": completed,
            "by_step": by_step,
            "completion_rate": round(completion_rate, 2),
        }

    async def get_deeplink_stats(self) -> dict:
        return await self.db.count_users_by_deep_link()

    async def get_weekly_deeplink_stats(self) -> dict:
        return await self.db.count_users_by_deep_link_since(self._week_ago_iso())

    async def get_step_distribution(self) -> dict:
        distribution = {}
        for step in STEPS:
            counts = await self.db.count_submissions_by_step_status(step)
            approved = counts.get("approved", 0)
            rejected = counts.get("rejected", 0)
            pending = counts.get("pending", 0)
            distribution[f"step{step}"] = {
                "total": approved + rejected + pending,
                "approved": approved,
                "rejected": rejected,
                "pending": pending,
            }
        return distribution
