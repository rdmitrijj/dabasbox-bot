"""Order id generation, local order log and admin chat notification."""

from __future__ import annotations

import asyncio
import json
import logging
import secrets
from datetime import datetime, timezone
from pathlib import Path

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from aiogram.types import InputMediaPhoto

from ..order import Order

logger = logging.getLogger(__name__)


def generate_order_id(now: datetime | None = None) -> str:
    """e.g. 260928-A3F9 — date for managers' orientation plus a random suffix for uniqueness."""
    now = now or datetime.now(timezone.utc)
    return f"{now:%y%m%d}-{secrets.token_hex(2).upper()}"


class OrderLog:
    """Append-only JSONL file so that no confirmed order is ever lost, even if Telegram delivery fails."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._lock = asyncio.Lock()

    async def append(self, order: Order, status: str) -> None:
        record = order.to_record()
        record["status"] = status
        record["logged_at"] = datetime.now(timezone.utc).isoformat()
        line = json.dumps(record, ensure_ascii=False)
        async with self._lock:
            await asyncio.to_thread(self._write_line, line)

    def _write_line(self, line: str) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")


async def _call_with_retry(coro_factory, attempts: int = 3):
    for attempt in range(1, attempts + 1):
        try:
            return await coro_factory()
        except TelegramRetryAfter as exc:
            if attempt == attempts:
                raise
            await asyncio.sleep(exc.retry_after + 0.5)


async def send_photos(bot: Bot, chat_id: int, photos: tuple[str, ...] | list[str], caption: str) -> None:
    """One photo as a photo, several as an album; the caption goes on the first one."""
    if len(photos) == 1:
        await _call_with_retry(lambda: bot.send_photo(chat_id, photos[0], caption=caption))
    elif photos:
        media = [InputMediaPhoto(media=file_id) for file_id in photos]
        media[0] = InputMediaPhoto(media=photos[0], caption=caption)
        await _call_with_retry(lambda: bot.send_media_group(chat_id, media=media))


async def notify_admins(bot: Bot, admin_chat_id: int, order: Order) -> None:
    """Send the order card and its photos to the management chat.

    The text card is mandatory (errors propagate so the caller can let the customer retry).
    Photos are best effort: if the album fails the managers get a follow-up note instead.
    """
    text = order.admin_notification_html()
    await _call_with_retry(lambda: bot.send_message(admin_chat_id, text, disable_web_page_preview=True))

    if not order.photos:
        return
    try:
        await send_photos(bot, admin_chat_id, order.photos, f"#DABASBOX-{order.order_id}")
    except TelegramAPIError:
        logger.exception("Failed to send photos for order %s", order.order_id)
        try:
            await bot.send_message(
                admin_chat_id,
                f"⚠️ Photos for #DABASBOX-{order.order_id} could not be attached. "
                f"Please contact the customer (user id {order.telegram_user_id}).",
            )
        except TelegramAPIError:
            logger.exception("Failed to send photo failure note for order %s", order.order_id)
