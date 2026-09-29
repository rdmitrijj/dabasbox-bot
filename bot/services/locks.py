"""Per-user asyncio locks.

aiogram processes updates concurrently. A photo album arrives as several updates at
once, and a user may double-tap "Confirm". Serialising read-modify-write on FSM data
per user avoids lost photos and duplicate orders.

Note: these locks are process-local. When running several bot instances against one
Redis, route each user to a single instance (default for long polling with one process).
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager


class UserLocks:
    def __init__(self) -> None:
        self._locks: dict[int, asyncio.Lock] = {}
        self._waiters: dict[int, int] = {}

    @asynccontextmanager
    async def hold(self, user_id: int) -> AsyncIterator[None]:
        lock = self._locks.setdefault(user_id, asyncio.Lock())
        self._waiters[user_id] = self._waiters.get(user_id, 0) + 1
        try:
            async with lock:
                yield
        finally:
            self._waiters[user_id] -= 1
            if self._waiters[user_id] == 0:
                # No one else is waiting: drop the lock so the dict doesn't grow forever.
                del self._waiters[user_id]
                del self._locks[user_id]
