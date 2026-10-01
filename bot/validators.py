"""Pure input validation / parsing functions. Each returns a parsed value or raises ValidationError."""

from __future__ import annotations

import re
from dataclasses import dataclass


class ValidationError(ValueError):
    """Raised with a translation key (see bot/locales) explaining what is wrong with the input."""

    def __init__(self, key: str, **params: object) -> None:
        super().__init__(key)
        self.key = key
        self.params = params


# --------------------------------------------------------------------------- dimensions

# Separators: Latin x/X, Cyrillic х/Х, multiplication sign ×, comma, asterisk.
DIMENSIONS_RE = re.compile(
    r"^(\d{3,4})\s*[×xхXХ,*]\s*(\d{3,4})\s*[×xхXХ,*]\s*(\d{3,4})$"
)


@dataclass(frozen=True)
class Dimensions:
    height: int
    width: int
    depth: int


def parse_dimensions(text: str) -> Dimensions:
    cleaned = re.sub(r"\s*mm\s*$", "", text.strip(), flags=re.IGNORECASE)
    match = DIMENSIONS_RE.match(cleaned)
    if not match:
        raise ValidationError("err_dims_format")
    if any(group.startswith("0") for group in match.groups()):
        raise ValidationError("err_dims_leading_zero")
    height, width, depth = (int(group) for group in match.groups())
    return Dimensions(height, width, depth)


# --------------------------------------------------------------------------- colours

RAL_RE = re.compile(r"^RAL\s*(?:\d{4}|\d{3}\s?\d{2}\s?\d{2})$", re.IGNORECASE)  # RAL Classic / RAL Design
NCS_RE = re.compile(r"^(?:NCS\s*)?S?\s*\d{4}\s*-\s*(?:N|[GYRB](?:\d{2}[GYRB])?)$", re.IGNORECASE)
COLOR_NAME_RE = re.compile(r"^[\w\s\-./#()'’]+$", re.UNICODE)


def parse_custom_color(text: str) -> str:
    value = re.sub(r"\s+", " ", text.strip())
    if len(value) < 3:
        raise ValidationError("err_color_short")
    if len(value) > 60:
        raise ValidationError("err_color_long")

    upper = value.upper()
    if upper.startswith("RAL"):
        if not RAL_RE.match(value):
            raise ValidationError("err_ral")
        digits = re.sub(r"\D", "", value)
        return f"RAL {digits}" if len(digits) == 4 else f"RAL {digits[:3]} {digits[3:5]} {digits[5:]}"
    if upper.startswith("NCS"):
        if not NCS_RE.match(value):
            raise ValidationError("err_ncs")
        return upper
    if not COLOR_NAME_RE.match(value) or not re.search(r"[^\W\d_]", value):
        raise ValidationError("err_color_name")
    return value


# --------------------------------------------------------------------------- country

COUNTRY_RE = re.compile(r"^[^\W\d_]+(?:[\s\-'’.][^\W\d_]+)*\.?$", re.UNICODE)


def parse_country(text: str) -> str:
    value = re.sub(r"\s+", " ", text.strip())
    if not 3 <= len(value) <= 56 or not COUNTRY_RE.match(value):
        raise ValidationError("err_country")
    return value[0].upper() + value[1:]


# --------------------------------------------------------------------------- address

# Country-specific postal code formats; anything else falls back to a generic pattern.
POSTAL_PATTERNS: dict[str, re.Pattern[str]] = {
    "Latvia": re.compile(r"\b(?:LV[\s-]?)?(\d{4})\b", re.IGNORECASE),
    "Lithuania": re.compile(r"\b(?:LT[\s-]?)?(\d{5})\b", re.IGNORECASE),
    "Estonia": re.compile(r"\b(?:EE[\s-]?)?(\d{5})\b", re.IGNORECASE),
}
POSTAL_PREFIX = {"Latvia": "LV-", "Lithuania": "LT-", "Estonia": ""}
GENERIC_POSTAL_RE = re.compile(r"\b[A-Z]{0,3}[\s-]?\d{2,5}(?:[\s-]\d{2,4})?\b|\b\d{4,6}\b", re.IGNORECASE)

MIN_ADDRESS_LENGTH = 10
MAX_ADDRESS_LENGTH = 300


@dataclass(frozen=True)
class Address:
    zip_code: str
    address: str


def _strip_separators(text: str) -> str:
    return re.sub(r"^[\s,;]+|[\s,;]+$", "", re.sub(r"\s*,\s*,\s*", ", ", text)).strip()


def parse_address(text: str, country: str) -> Address:
    value = re.sub(r"\s+", " ", text.strip())
    if len(value) < MIN_ADDRESS_LENGTH:
        raise ValidationError("err_address_short", min=MIN_ADDRESS_LENGTH)
    if len(value) > MAX_ADDRESS_LENGTH:
        raise ValidationError("err_address_long", max=MAX_ADDRESS_LENGTH)
    if not re.search(r"\d", value):
        raise ValidationError("err_address_no_digits")

    pattern = POSTAL_PATTERNS.get(country)
    if pattern is not None:
        match = pattern.search(value)
        if not match:
            example = {"Latvia": "LV-1010", "Lithuania": "LT-01103", "Estonia": "10111"}[country]
            raise ValidationError("err_postal_country", country=country, example=example)
        zip_code = POSTAL_PREFIX[country] + match.group(1)
    else:
        match = next(
            (m for m in GENERIC_POSTAL_RE.finditer(value) if len(re.sub(r"\D", "", m.group(0))) >= 3),
            None,
        )
        if not match:
            raise ValidationError("err_postal_missing")
        zip_code = match.group(0).strip().upper()

    rest = _strip_separators(value[: match.start()] + " " + value[match.end():])
    rest = re.sub(r"\s+", " ", rest).strip(" ,;")
    if len(re.sub(r"[\W_]", "", rest)) < 5:
        raise ValidationError("err_address_rest")
    return Address(zip_code=zip_code, address=rest)


# --------------------------------------------------------------------------- phone / name

E164_RE = re.compile(r"^\+?[1-9]\d{6,14}$")  # E.164: up to 15 digits; 7 is a sane minimum for real numbers
NAME_PART_RE = re.compile(r"^[^\W\d_]+(?:['’\-][^\W\d_]+)*\.?$", re.UNICODE)


def normalize_phone(raw: str) -> str:
    cleaned = re.sub(r"[\s\-().]", "", raw.strip())
    if cleaned.startswith("00"):
        cleaned = "+" + cleaned[2:]
    if not E164_RE.match(cleaned):
        raise ValidationError("err_phone")
    return cleaned if cleaned.startswith("+") else "+" + cleaned


def validate_name_part(value: str, label: str) -> str:
    value = value.strip()
    if not 1 <= len(value) <= 64 or not NAME_PART_RE.match(value):
        raise ValidationError("err_name_chars")
    return value[0].upper() + value[1:]


def parse_first_name(text: str) -> str:
    """One or more name parts, e.g. 'Anna' or 'Anna Maria'."""
    parts = text.split()
    if not parts or len(parts) > 3:
        raise ValidationError("err_name_chars")
    return " ".join(validate_name_part(part, "First name") for part in parts)


# --------------------------------------------------------------------------- e-mail

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s.]+(?:\.[^@\s.]+)*\.[^\W\d_]{2,}$", re.UNICODE)


def parse_email(text: str) -> str:
    value = text.strip()
    if len(value) > 254 or not EMAIL_RE.match(value):
        raise ValidationError("err_email")
    local, domain = value.rsplit("@", 1)
    return f"{local}@{domain.lower()}"
