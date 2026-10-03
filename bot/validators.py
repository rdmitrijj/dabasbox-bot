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

# Popular mailbox providers. A domain that is a near miss of one of these (gmail.co, gmial.com,
# inbox.lc, hotmal.com) is treated as a typo even if it exists: typo domains are often parked
# by squatters and *do* have mail servers. Real look-alike providers are listed so they pass.
# Most likely first: on a tie (inbox.lc is one letter from inbox.lv and inbox.lt) the earlier one wins.
KNOWN_EMAIL_DOMAINS = (
    "gmail.com", "inbox.lv", "outlook.com", "hotmail.com", "icloud.com", "yahoo.com", "mail.ru", "yandex.ru",
    # Baltics
    "inbox.lt", "inbox.eu", "tvnet.lv", "apollo.lv", "one.lv", "mail.ee", "hot.ee",
    # International
    "googlemail.com", "live.com", "msn.com", "ymail.com", "me.com", "mac.com", "aol.com",
    "proton.me", "protonmail.com", "protonmail.ch", "pm.me", "gmx.com", "gmx.net", "gmx.de", "web.de",
    "mail.com", "email.com", "mail.de", "zoho.com", "tutanota.com", "fastmail.com", "fastmail.fm",
    # Russian-speaking
    "inbox.ru", "list.ru", "bk.ru", "yandex.com", "ya.ru", "rambler.ru",
)
# Providers that use only these exact domains, so the same name with any other ending is a mistake
# (gmail.lv, gmail.co.uk, icloud.lv).
_SINGLE_DOMAIN_PROVIDERS = {"gmail": "gmail.com", "googlemail": "googlemail.com", "icloud": "icloud.com"}


def _edit_distance(a: str, b: str) -> int:
    """Levenshtein distance that also counts swapping two adjacent letters as one edit."""
    prev2: list[int] = []
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
            if i > 1 and j > 1 and ca == b[j - 2] and a[i - 2] == cb:
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        prev2, prev = prev, cur
    return prev[-1]


def suggest_email_domain(domain: str) -> str | None:
    """The popular domain the user most likely meant, or None if `domain` doesn't look like a typo."""
    if domain in KNOWN_EMAIL_DOMAINS:
        return None
    name = domain.split(".", 1)[0]
    if name in _SINGLE_DOMAIN_PROVIDERS:
        return _SINGLE_DOMAIN_PROVIDERS[name]
    tld = domain.rsplit(".", 1)[-1]
    best: tuple[int, str] | None = None
    for known in KNOWN_EMAIL_DOMAINS:
        # Very short domains are one letter away from too many real ones (ya.ru / yo.ru): skip them.
        # Two typos only count when the ending matches, so regional domains such as outlook.cz pass.
        if len(known) < 7:
            continue
        allowed = 2 if len(known) >= 11 and known.endswith(f".{tld}") else 1
        if abs(len(domain) - len(known)) <= allowed:
            distance = _edit_distance(domain, known)
            if distance <= allowed and (best is None or distance < best[0]):
                best = (distance, known)
    return best[1] if best else None


def parse_email(text: str) -> str:
    value = text.strip()
    if len(value) > 254 or not EMAIL_RE.match(value):
        raise ValidationError("err_email")
    local, domain = value.rsplit("@", 1)
    domain = domain.lower()
    suggestion = suggest_email_domain(domain)
    if suggestion:
        raise ValidationError("err_email_typo", suggestion=f"{local}@{suggestion}")
    return f"{local}@{domain}"
