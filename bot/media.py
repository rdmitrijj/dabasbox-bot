"""Optional step images.

Drop an image into bot/images/ named after a step (see STEPS) and the bot shows it at that
step, with the step's text as the caption. For several images, put them in a folder named after
the step (e.g. bot/images/color/): they are sent as an album, followed by the step's text.
No image file means a plain text message.

Language variants: an image named <name>.<lang>.<ext> (e.g. pumpinfo.lv.png) replaces <name>.<ext>
for users of that language and is never shown to the others.
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

from .i18n import LANGUAGES

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
    "email": "asking for the e-mail address",
    "phone": "asking for the phone number",
    "name": "asking for the first name",
    "payment": "payment method buttons (cash / bank transfer)",
}

# Telegram file_id per uploaded image, so each file is uploaded only once per process.
_file_ids: dict[tuple[Path, int], str] = {}

Markup = InlineKeyboardMarkup | ReplyKeyboardMarkup | ReplyKeyboardRemove | None


def _split_language(image: Path) -> tuple[str, str | None]:
    """'pumpinfo.lv.png' -> ('pumpinfo', 'lv'); 'pumpinfo.png' -> ('pumpinfo', None)."""
    name, _, tag = image.stem.rpartition(".")
    return (name, tag) if name and tag in LANGUAGES else (image.stem, None)


def _for_language(images: list[Path], lang: str | None) -> list[Path]:
    """Drop other languages' variants and let `lang`'s variant replace the image of the same name."""
    chosen: dict[str, Path] = {}
    for image in images:
        name, tag = _split_language(image)
        if tag is None:
            chosen.setdefault(name, image)
        elif tag == lang:
            chosen[name] = image
    return [chosen[name] for name in sorted(chosen)]


def step_image(step: str, lang: str | None = None) -> Path | None:
    names = ([f"{step}.{lang}"] if lang else []) + [step]
    for name in names:
        for ext in EXTENSIONS:
            path = IMAGES_DIR / f"{name}{ext}"
            if path.is_file():
                return path
    return None


def step_album(step: str, lang: str | None = None) -> list[Path]:
    """Images in bot/images/<step>/ for `lang`, sorted by file name."""
    folder = IMAGES_DIR / step
    if not folder.is_dir():
        return []
    images = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS]
    return _for_language(images, lang)[:ALBUM_LIMIT]


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


async def send_step(
    message: Message, step: str, text: str, reply_markup: Markup = None, *, lang: str | None = None
) -> Message:
    """Send `text` for `step`, as a photo caption if bot/images/<step>.<ext> exists.

    If bot/images/<step>/ holds images, they go first as an album (albums can't carry buttons),
    then `text` with `reply_markup` as a separate message. `lang` picks language variants.
    """
    album = step_album(step, lang)
    if len(album) > 1:  # Telegram albums need 2-10 items
        await _send_album(message, album)
        return await message.answer(text, reply_markup=reply_markup)

    image = album[0] if album else step_image(step, lang)
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
