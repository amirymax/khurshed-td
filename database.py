"""SQLite persistence layer for the bot (async, via aiosqlite)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    current_step INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    deep_link_source TEXT,
    flow_type TEXT DEFAULT 'course',
    group1_status TEXT DEFAULT 'not_joined',
    group2_status TEXT DEFAULT 'not_joined',
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    step INTEGER NOT NULL,
    submission_type TEXT,
    submission_value TEXT,
    submitted_at TIMESTAMP,
    admin_decision TEXT DEFAULT 'pending',
    rejection_reason TEXT,
    admin_id INTEGER,
    admin_decision_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE IF NOT EXISTS group_invites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    invite_link TEXT UNIQUE,
    created_at TIMESTAMP,
    expires_at TIMESTAMP,
    used INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    """Thin async wrapper around the SQLite database used by the bot."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._conn.executescript(SCHEMA)
        try:
            await self._conn.execute("ALTER TABLE users ADD COLUMN flow_type TEXT DEFAULT 'course'")
        except aiosqlite.OperationalError:
            pass  # column already exists (pre-existing database file)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database is not connected. Call connect() first.")
        return self._conn

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    async def get_user(self, user_id: int) -> Optional[dict[str, Any]]:
        cursor = await self.conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def create_user(
        self, user_id: int, username: str | None, deep_link_source: str = "organic"
    ) -> dict[str, Any]:
        existing = await self.get_user(user_id)
        if existing:
            return existing
        now = _now()
        await self.conn.execute(
            """INSERT INTO users
               (user_id, username, current_step, status, deep_link_source,
                group1_status, group2_status, created_at, updated_at)
               VALUES (?, ?, 0, 'pending', ?, 'not_joined', 'not_joined', ?, ?)""",
            (user_id, username, deep_link_source, now, now),
        )
        await self.conn.commit()
        return await self.get_user(user_id)

    async def update_user(self, user_id: int, **fields: Any) -> None:
        if not fields:
            return
        fields["updated_at"] = _now()
        columns = ", ".join(f"{key} = ?" for key in fields)
        values = list(fields.values()) + [user_id]
        await self.conn.execute(
            f"UPDATE users SET {columns} WHERE user_id = ?", values
        )
        await self.conn.commit()

    async def set_current_step(self, user_id: int, step: int) -> None:
        await self.update_user(user_id, current_step=step)

    async def set_group_status(self, user_id: int, group: int, status: str) -> None:
        column = "group1_status" if group == 1 else "group2_status"
        await self.update_user(user_id, **{column: status})

    async def get_all_users(self) -> list[dict[str, Any]]:
        cursor = await self.conn.execute("SELECT * FROM users")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Submissions
    # ------------------------------------------------------------------
    async def create_submission(
        self,
        user_id: int,
        step: int,
        submission_type: str,
        submission_value: str,
    ) -> int:
        now = _now()
        cursor = await self.conn.execute(
            """INSERT INTO submissions
               (user_id, step, submission_type, submission_value,
                submitted_at, admin_decision)
               VALUES (?, ?, ?, ?, ?, 'pending')""",
            (user_id, step, submission_type, submission_value, now),
        )
        await self.conn.commit()
        return cursor.lastrowid

    async def get_submission(self, submission_id: int) -> Optional[dict[str, Any]]:
        cursor = await self.conn.execute(
            "SELECT * FROM submissions WHERE id = ?", (submission_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def decide_submission(
        self,
        submission_id: int,
        decision: str,
        admin_id: int,
        rejection_reason: str | None = None,
    ) -> None:
        await self.conn.execute(
            """UPDATE submissions
               SET admin_decision = ?, rejection_reason = ?, admin_id = ?, admin_decision_at = ?
               WHERE id = ?""",
            (decision, rejection_reason, admin_id, _now(), submission_id),
        )
        await self.conn.commit()

    async def get_pending_submissions(self, steps: list[int]) -> list[dict[str, Any]]:
        placeholders = ",".join("?" for _ in steps)
        cursor = await self.conn.execute(
            f"""SELECT s.*, u.username, u.flow_type FROM submissions s
                JOIN users u ON u.user_id = s.user_id
                WHERE s.admin_decision = 'pending' AND s.step IN ({placeholders})
                ORDER BY s.submitted_at ASC""",
            steps,
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_submissions_by_step(self, step: int) -> list[dict[str, Any]]:
        cursor = await self.conn.execute(
            "SELECT * FROM submissions WHERE step = ?", (step,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Group invites
    # ------------------------------------------------------------------
    async def add_invite(
        self,
        user_id: int,
        group_id: int,
        invite_link: str,
        expires_at: str | None = None,
    ) -> None:
        await self.conn.execute(
            """INSERT INTO group_invites (user_id, group_id, invite_link, created_at, expires_at, used)
               VALUES (?, ?, ?, ?, ?, 0)""",
            (user_id, group_id, invite_link, _now(), expires_at),
        )
        await self.conn.commit()

    async def get_invites_for_user(self, user_id: int) -> list[dict[str, Any]]:
        cursor = await self.conn.execute(
            "SELECT * FROM group_invites WHERE user_id = ?", (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def mark_invite_used(self, invite_link: str) -> None:
        await self.conn.execute(
            "UPDATE group_invites SET used = 1 WHERE invite_link = ?", (invite_link,)
        )
        await self.conn.commit()

    # ------------------------------------------------------------------
    # Analytics helpers (raw data access; aggregation lives in utils/analytics.py)
    # ------------------------------------------------------------------
    async def count_users(self) -> int:
        cursor = await self.conn.execute("SELECT COUNT(*) AS c FROM users")
        row = await cursor.fetchone()
        return row["c"]

    async def count_users_since(self, since_iso: str) -> int:
        cursor = await self.conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE created_at >= ?", (since_iso,)
        )
        row = await cursor.fetchone()
        return row["c"]

    async def count_users_by_step(self, step: int) -> int:
        cursor = await self.conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE current_step = ?", (step,)
        )
        row = await cursor.fetchone()
        return row["c"]

    async def count_users_by_deep_link(self) -> dict[str, int]:
        cursor = await self.conn.execute(
            "SELECT deep_link_source, COUNT(*) AS c FROM users GROUP BY deep_link_source"
        )
        rows = await cursor.fetchall()
        return {row["deep_link_source"] or "organic": row["c"] for row in rows}

    async def count_users_by_deep_link_since(self, since_iso: str) -> dict[str, int]:
        cursor = await self.conn.execute(
            "SELECT deep_link_source, COUNT(*) AS c FROM users WHERE created_at >= ? GROUP BY deep_link_source",
            (since_iso,),
        )
        rows = await cursor.fetchall()
        return {row["deep_link_source"] or "organic": row["c"] for row in rows}

    async def count_submissions_by_step_status(self, step: int) -> dict[str, int]:
        cursor = await self.conn.execute(
            "SELECT admin_decision, COUNT(*) AS c FROM submissions WHERE step = ? GROUP BY admin_decision",
            (step,),
        )
        rows = await cursor.fetchall()
        return {row["admin_decision"]: row["c"] for row in rows}

    async def count_completed_users(self) -> int:
        cursor = await self.conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE status = 'completed'"
        )
        row = await cursor.fetchone()
        return row["c"]
