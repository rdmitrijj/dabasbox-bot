"""Translations: language registry, per-user language storage and the `t` translator.

To add a language: copy locales/en.py to locales/<code>.py, translate the values, and add it
to LANGUAGES below. Handlers receive `t` (a Translator for the user's language) automatically.
"""

from __future__ import annotations

import string
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.fsm.storage.base import BaseStorage, StorageKey
from aiogram.types import TelegramObject, User

from .locales import en, lv, ru

# code -> locale module. The first entry is the fallback for missing keys.
LANGUAGES = {"en": en, "lv": lv, "ru": ru}
DEFAULT_LANGUAGE = "en"

# Shown before a language is known, so it is written in every language at once.
CHOOSE_LANGUAGE = "🌐 Choose your language / Izvēlieties valodu / Выберите язык:"


class Translator:
    def __init__(self, lang: str) -> None:
        self.lang = lang if lang in LANGUAGES else DEFAULT_LANGUAGE
        self._texts = LANGUAGES[self.lang].TEXTS
        self._fallback = LANGUAGES[DEFAULT_LANGUAGE].TEXTS

    def __call__(self, key: str, **params: Any) -> str:
        text = self._texts.get(key) or self._fallback[key]
        return text.format(**params) if params else text

    def country(self, canonical: str) -> str:
        """Localised name for the built-in countries (stored in English); other names as typed."""
        from .catalog import COUNTRIES

        for key, name in COUNTRIES.items():
            if name == canonical:
                return self(f"country_{key}")
        return canonical


def placeholders(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


# ------------------------------------------------------------------ per-user language storage

def _key(bot_id: int, user_id: int) -> StorageKey:
    # A separate "destiny" keeps the language outside the order data, so /start and /cancel don't reset it.
    return StorageKey(bot_id=bot_id, chat_id=user_id, user_id=user_id, destiny="language")


async def get_saved_language(storage: BaseStorage, bot_id: int, user_id: int) -> str | None:
    lang = (await storage.get_data(_key(bot_id, user_id))).get("lang")
    return lang if lang in LANGUAGES else None


async def save_language(storage: BaseStorage, bot_id: int, user_id: int, lang: str) -> None:
    await storage.set_data(_key(bot_id, user_id), {"lang": lang})


class LanguageMiddleware(BaseMiddleware):
    """Injects `t` (Translator) and `lang_chosen` (bool) into every handler."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        saved = None
        if user is not None:
            saved = await get_saved_language(data["fsm_storage"], data["bot"].id, user.id)
        data["lang_chosen"] = saved is not None
        data["t"] = Translator(saved or DEFAULT_LANGUAGE)
        return await handler(event, data)
