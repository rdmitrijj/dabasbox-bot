"""Optional step images.

Drop an image into bot/images/ named after a step (see STEPS) and the bot shows it at that
step, with the step's text as the caption. No image file means a plain text message.
"""

from __future__ import annotations

import html
import logging
import re
from pathlib import Path

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import FSInputFile, InlineKeyboardMarkup, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

logger = logging.getLogger(__name__)

IMAGES_DIR = Path(__file__).resolve().parent / "images"
EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
CAPTION_LIMIT = 1024

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


def _visible_length(html_text: str) -> int:
    return len(html.unescape(re.sub(r"<[^>]+>", "", html_text)))


async def send_step(message: Message, step: str, text: str, reply_markup: Markup = None) -> Message:
    """Send `text` for `step`, as a photo caption if bot/images/<step>.<ext> exists."""
    image = step_image(step)
    if image is None:
        return await message.answer(text, reply_markup=reply_markup)

    key = (image, image.stat().st_mtime_ns)  # a replaced file gets uploaded again
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
