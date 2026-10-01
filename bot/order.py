"""Order model assembled from FSM data, plus summary / admin notification formatting."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any

from .catalog import PAYMENT_METHODS
from .pricing import CATEGORY_BY_CODE, color_surcharge, total_price
from .utils import escape

if TYPE_CHECKING:
    from .i18n import Translator


LANGUAGE_NAMES = {"en": "English", "lv": "Latvian", "ru": "Russian"}


class IncompleteOrderError(RuntimeError):
    """FSM data is missing a required field (e.g. state storage was reset mid-flow)."""


@dataclass(frozen=True)
class Order:
    height: int
    width: int
    depth: int
    category: str | None  # None => individual manager calculation
    out_of_range: tuple[str, ...]
    photos: tuple[str, ...]
    color_name: str
    custom_color: bool
    country: str
    zip_code: str
    address: str
    email: str
    phone: str
    first_name: str
    payment: str  # key in catalog.PAYMENT_METHODS
    color_key: str | None = None  # key in catalog.BASE_COLORS, or "custom"
    custom_color_code: str | None = None
    language: str | None = None  # customer's bot language code
    telegram_user_id: int | None = None
    telegram_username: str | None = None
    order_id: str | None = field(default=None)

    # ---------------------------------------------------------------- construction

    REQUIRED = (
        "height", "width", "depth", "photos", "color_name", "custom_color",
        "country", "zip_code", "address", "email", "phone", "first_name", "payment",
    )

    @classmethod
    def from_fsm(cls, data: dict[str, Any]) -> Order:
        missing = [key for key in cls.REQUIRED if data.get(key) in (None, "", [])]
        if missing:
            raise IncompleteOrderError(f"missing fields: {', '.join(missing)}")
        category = data.get("category")
        if category is not None and category not in CATEGORY_BY_CODE:
            raise IncompleteOrderError(f"unknown category {category!r}")
        if data["payment"] not in PAYMENT_METHODS:
            raise IncompleteOrderError(f"unknown payment method {data['payment']!r}")
        return cls(
            height=int(data["height"]),
            width=int(data["width"]),
            depth=int(data["depth"]),
            category=category,
            out_of_range=tuple(data.get("out_of_range") or ()),
            photos=tuple(data["photos"]),
            color_name=str(data["color_name"]),
            custom_color=bool(data["custom_color"]),
            country=str(data["country"]),
            zip_code=str(data["zip_code"]),
            address=str(data["address"]),
            email=str(data["email"]),
            phone=str(data["phone"]),
            first_name=str(data["first_name"]),
            payment=str(data["payment"]),
            color_key=data.get("color_key"),
            custom_color_code=data.get("custom_color_code"),
        )

    # ---------------------------------------------------------------- pricing

    @property
    def needs_manual_calculation(self) -> bool:
        return self.category is None

    @property
    def base_price(self) -> int | None:
        return CATEGORY_BY_CODE[self.category].base_price if self.category else None

    @property
    def color_surcharge(self) -> int:
        return color_surcharge(self.custom_color)

    @property
    def total_price(self) -> int | None:
        return total_price(self.base_price, self.custom_color)

    def to_record(self) -> dict[str, Any]:
        record = asdict(self)
        record.update(base_price=self.base_price, color_surcharge=self.color_surcharge, total_price=self.total_price)
        return record

    # ---------------------------------------------------------------- formatting helpers

    def _color_surcharge_text(self) -> str:
        return f"(+{self.color_surcharge} €)" if self.custom_color else "(0 €, included)"

    def _category_line(self) -> str:
        if self.needs_manual_calculation:
            return "⚠️ Individual Manager Calculation (dimensions outside the standard size range)"
        return f"{self.category} (Base price: {self.base_price} €) [excl. 21% VAT]"

    def _total_line(self) -> str:
        if self.needs_manual_calculation:
            extra = f" (+{self.color_surcharge} € custom colour surcharge applies)" if self.custom_color else ""
            return f"TO BE CALCULATED BY A MANAGER{extra}"
        return f"{self.total_price} € (excl. 21% VAT)"

    def _out_of_range_block(self) -> str:
        if not self.out_of_range:
            return ""
        return "\n" + "\n".join(f"   • {escape(item)}" for item in self.out_of_range)

    # ---------------------------------------------------------------- user summary (translated)

    def _display_color(self, t: Translator) -> str:
        if self.custom_color and self.custom_color_code:
            return t("color_custom_name", code=escape(self.custom_color_code))
        if self.color_key:
            return t(f"color_{self.color_key}")
        return escape(self.color_name)

    def summary_html(self, t: Translator) -> str:
        e = escape
        surcharge = (
            t("surcharge_custom", surcharge=self.color_surcharge) if self.custom_color else t("surcharge_included")
        )
        if self.needs_manual_calculation:
            category = t("sum_category_manual")
            total = (
                t("sum_total_manual_custom", surcharge=self.color_surcharge)
                if self.custom_color
                else t("sum_total_manual")
            )
        else:
            category = t("sum_category", category=self.category, price=self.base_price)
            total = t("sum_total", total=self.total_price) + "\n" + t(
                "sum_breakdown", base=self.base_price, surcharge=self.color_surcharge
            )
        return "\n".join(
            [
                t("summary_title"),
                "",
                t("sum_dims", h=self.height, w=self.width, d=self.depth),
                category,
                t("sum_photos", count=len(self.photos)),
                "",
                t("sum_color", color=self._display_color(t), surcharge=surcharge),
                "",
                t("sum_country", country=e(t.country(self.country))),
                t("sum_address", zip=e(self.zip_code), address=e(self.address)),
                "",
                t("sum_contact", name=e(self.first_name)),
                t("sum_email", email=e(self.email)),
                t("sum_phone", phone=e(self.phone)),
                t("sum_payment", payment=t(f"payment_{self.payment}")),
                "",
                total,
                "",
                t("sum_check"),
            ]
        )

    # ---------------------------------------------------------------- admin notification

    def admin_notification_html(self) -> str:
        if self.order_id is None:
            raise IncompleteOrderError("order_id must be assigned before notifying admins")
        e = escape
        if self.telegram_username:
            tg = f"@{e(self.telegram_username)} (id {self.telegram_user_id})"
        else:
            tg = f'<a href="tg://user?id={self.telegram_user_id}">id {self.telegram_user_id}</a>'
        return "\n".join(
            [
                f"📦 <b>NEW ORDER #DABASBOX-{e(self.order_id)}</b>",
                "",
                f"👤 Customer: {e(self.first_name)}",
                f"📧 Email: {e(self.email)}",
                f"📞 Phone: {e(self.phone)}",
                f"💬 Telegram: {tg}",
                *([f"🗣 Language: {e(LANGUAGE_NAMES.get(self.language, self.language))}"] if self.language else []),
                f"🌍 Country: {e(self.country)}",
                f"🏠 Postal Code &amp; Address: {e(self.zip_code)}, {e(self.address)}",
                "",
                f"📐 Heat Pump Net Dimensions: {self.height} mm (H) x {self.width} mm (W) x {self.depth} mm (D)",
                f"🏷 Determined Category: {e(self._category_line())}{self._out_of_range_block()}",
                "",
                f"🎨 Color: {e(self.color_name)} {e(self._color_surcharge_text())}",
                f"💰 <b>TOTAL PRICE: {e(self._total_line())}</b>",
                f"💳 Payment: {e(PAYMENT_METHODS[self.payment])}",
                "",
                f"🖼 Photos attached below ({len(self.photos)} pcs)",
            ]
        )
