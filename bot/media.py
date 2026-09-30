"""Optional step images.

Drop an image into bot/images/ named after a step (see STEPS) and the bot shows it at that
step, with the step's text as the caption. For several images, put them in a folder named after
the step (e.g. bot/images/color/): they are sent as an album, followed by the step's text.
No image file means a plain text message.
"""

from __future__ import annotations

import html
import logging
import re
from pathlib import Path

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    FSInputFile,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

logger = logging.getLogger(__name__)

IMAGES_DIR = Path(__file__).resolve().parent / "images"
EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
CAPTION_LIMIT = 1024
ALBUM_LIMIT = 10  # Telegram's maximum for one media group

# File name (without extension) -> where it is shown.
STEPS = {
    "start": "welcome and measuring instructions (/start)",
    "dimensions": "asking for Height x Width x Depth",
    "photos": "asking the customer to upload photos",
    "color": "colour choice buttons",
    "custom_color": "asking for a RAL / NCS code",
    "country": "country choice buttons",
    "address": "asking for postal code and address",
    "contact": "asking for name and phone",
}

# Telegram file_id per uploaded image, so each file is uploaded only once per process.
_file_ids: dict[tuple[Path, int], str] = {}

Markup = InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | None


def step_image(step: str) -> Path | None:
    for ext in EXTENSIONS:
        path = IMAGES_DIR / f"{step}{ext}"
        if path.is_file():
            return path
    return None


def step_album(step: str) -> list[Path]:
    """Images in bot/images/<step>/, sorted by file name."""
    folder = IMAGES_DIR / step
    if not folder.is_dir():
        return []
    images = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS)
    return images[:ALBUM_LIMIT]


def _cache_key(image: Path) -> tuple[Path, int]:
    return (image, image.stat().st_mtime_ns)  # a replaced file gets uploaded again


async def _send_album(message: Message, images: list[Path]) -> None:
    keys = [_cache_key(image) for image in images]
    media = [InputMediaPhoto(media=_file_ids.get(key) or FSInputFile(key[0])) for key in keys]
    try:
        sent = await message.answer_media_group(media)
    except TelegramBadRequest:
        logger.exception("Could not send step album %s", images[0].parent)
        for key in keys:
            _file_ids.pop(key, None)
        return
    for key, msg in zip(keys, sent):
        if msg.photo:
            _file_ids[key] = msg.photo[-1].file_id


def _visible_length(html_text: str) -> int:
    return len(html.unescape(re.sub(r"<[^>]+>", "", html_text)))


async def send_step(message: Message, step: str, text: str, reply_markup: Markup = None) -> Message:
    """Send `text` for `step`, as a photo caption if bot/images/<step>.<ext> exists.

    If bot/images/<step>/ holds images, they go first as an album (albums can't carry buttons),
    then `text` with `reply_markup` as a separate message.
    """
    album = step_album(step)
    if len(album) > 1:  # Telegram albums need 2-10 items
        await _send_album(message, album)
        return await message.answer(text, reply_markup=reply_markup)

    image = album[0] if album else step_image(step)
    if image is None:
        return await message.answer(text, reply_markup=reply_markup)

    key = _cache_key(image)
    photo = _file_ids.get(key) or FSInputFile(image)
    fits = _visible_length(text) <= CAPTION_LIMIT
    try:
        sent = await message.answer_photo(
            photo, caption=text if fits else None, reply_markup=reply_markup if fits else None
        )
    except TelegramBadRequest:
        logger.exception("Could not send step image %s; falling back to text", image)
        _file_ids.pop(key, None)
        return await message.answer(text, reply_markup=reply_markup)

    if sent.photo:
        _file_ids[key] = sent.photo[-1].file_id
    if not fits:  # too long for a caption: photo first, then the text with the buttons
        return await message.answer(text, reply_markup=reply_markup)
    return sent
