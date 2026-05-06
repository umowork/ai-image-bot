"""
Rate limiting middleware for aiogram 3.
Prevents spam: max N messages per user per time window.
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict

from aiogram import BaseMiddleware
from aiogram.types import Message

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    """Simple in-memory rate limiter per user."""

    def __init__(
        self,
        max_messages: int = 5,
        window_seconds: float = 10.0,
    ):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self._user_timestamps: dict[int, list[float]] = defaultdict(list)

    async def __call__(self, handler, event: Message, data: dict) -> bool | None:
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id
        now = time.monotonic()

        # Clean old timestamps
        self._user_timestamps[user_id] = [
            ts for ts in self._user_timestamps[user_id]
            if now - ts < self.window_seconds
        ]

        if len(self._user_timestamps[user_id]) >= self.max_messages:
            remaining = self.window_seconds - (
                now - self._user_timestamps[user_id][0]
            )
            await event.answer(
                f"⏳ Слишком много запросов. Подожди {remaining:.0f} сек."
            )
            logger.warning("rate limit hit: user=%d", user_id)
            return None  # block handler

        self._user_timestamps[user_id].append(now)
        return await handler(event, data)
