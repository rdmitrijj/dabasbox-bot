from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from .catalog import BASE_COLORS, COUNTRIES
from .i18n import LANGUAGES, Translator
from .pricing import CUSTOM_COLOR_SURCHARGE


class NavCb(CallbackData, prefix="nav"):
    action: str  # proceed_dimensions | photos_done | photos_reset | confirm | cancel


class ColorCb(CallbackData, prefix="color"):
    key: str  # key from BASE_COLORS or "custom"


class CountryCb(CallbackData, prefix="country"):
    key: str  # key from COUNTRIES or "other"


class LangCb(CallbackData, prefix="lang"):
    code: str  # key from i18n.LANGUAGES


def language_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=module.NAME, callback_data=LangCb(code=code).pack())]
            for code, module in LANGUAGES.items()
        ]
    )


def instruction_ack_kb(t: Translator) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t("btn_proceed"), callback_data=NavCb(action="proceed_dimensions").pack())]]
    )


def photos_kb(t: Translator, photo_count: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if photo_count >= 1:
        rows.append([InlineKeyboardButton(text=t("btn_photos_done"), callback_data=NavCb(action="photos_done").pack())])
    rows.append([InlineKeyboardButton(text=t("btn_photos_reset"), callback_data=NavCb(action="photos_reset").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def color_kb(t: Translator) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{t(f'color_{key}')} (0€)", callback_data=ColorCb(key=key).pack())]
        for key in BASE_COLORS
    ]
    rows.append(
        [
            InlineKeyboardButton(
                text=t("btn_custom_color", surcharge=CUSTOM_COLOR_SURCHARGE),
                callback_data=ColorCb(key="custom").pack(),
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def country_kb(t: Translator) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=t(f"country_{key}"), callback_data=CountryCb(key=key).pack())] for key in COUNTRIES]
    rows.append([InlineKeyboardButton(text=t("country_other"), callback_data=CountryCb(key="other").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def contact_kb(t: Translator) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("btn_share_contact"), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="John Smith +37120000000",
    )


def confirmation_kb(t: Translator) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_confirm"), callback_data=NavCb(action="confirm").pack())],
            [InlineKeyboardButton(text=t("btn_cancel"), callback_data=NavCb(action="cancel").pack())],
        ]
    )
