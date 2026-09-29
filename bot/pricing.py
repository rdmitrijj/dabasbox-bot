"""Dabasbox size matrix, category determination and price calculation.

All prices are in whole euros, excluding 21% VAT.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

CUSTOM_COLOR_SURCHARGE = 30


class Axis(str, Enum):
    HEIGHT = "height"
    WIDTH = "width"
    DEPTH = "depth"


@dataclass(frozen=True)
class SizeCategory:
    code: str
    height: tuple[int, int]
    width: tuple[int, int]
    depth: tuple[int, int]
    base_price: int

    def bounds(self, axis: Axis) -> tuple[int, int]:
        return getattr(self, axis.value)


# Ordered from smallest to largest; the order is significant for category resolution.
CATEGORIES: tuple[SizeCategory, ...] = (
    SizeCategory("S", (680, 780), (720, 870), (420, 480), 250),
    SizeCategory("M", (780, 930), (880, 1020), (450, 500), 280),
    SizeCategory("L", (930, 1130), (970, 1120), (480, 540), 320),
    SizeCategory("XL", (1130, 1230), (1020, 1220), (520, 620), 360),
    SizeCategory("XXL", (1230, 1430), (1120, 1320), (520, 820), 420),
)

CATEGORY_BY_CODE = {c.code: c for c in CATEGORIES}

MIN_DIMENSIONS = {axis: CATEGORIES[0].bounds(axis)[0] for axis in Axis}
MAX_DIMENSIONS = {axis: CATEGORIES[-1].bounds(axis)[1] for axis in Axis}


@dataclass(frozen=True)
class OutOfRange:
    axis: Axis
    value: int
    limit: int
    too_large: bool

    def describe(self) -> str:
        relation = "above the maximum" if self.too_large else "below the minimum"
        return f"{self.axis.value.capitalize()} {self.value} mm is {relation} of {self.limit} mm"


@dataclass(frozen=True)
class SizeResult:
    height: int
    width: int
    depth: int
    category: SizeCategory | None
    out_of_range: tuple[OutOfRange, ...] = ()

    @property
    def needs_manual_calculation(self) -> bool:
        return self.category is None

    @property
    def base_price(self) -> int | None:
        return self.category.base_price if self.category else None


def _category_index_for(axis: Axis, value: int) -> int:
    """Index of the smallest category whose upper bound on `axis` covers `value`.

    The catalogue ranges overlap and leave small gaps (e.g. width 871-879 mm lies
    between S and M). Picking the smallest category whose upper bound is not
    exceeded closes those gaps upwards, so the enclosure is never too small.
    Caller guarantees `value` is within the global S-min..XXL-max range.
    """
    for index, category in enumerate(CATEGORIES):
        if value <= category.bounds(axis)[1]:
            return index
    raise ValueError(f"{axis.value}={value} exceeds the largest category")  # guarded by caller


def classify(height: int, width: int, depth: int) -> SizeResult:
    values = {Axis.HEIGHT: height, Axis.WIDTH: width, Axis.DEPTH: depth}

    problems: list[OutOfRange] = []
    for axis, value in values.items():
        if value > MAX_DIMENSIONS[axis]:
            problems.append(OutOfRange(axis, value, MAX_DIMENSIONS[axis], too_large=True))
        elif value < MIN_DIMENSIONS[axis]:
            problems.append(OutOfRange(axis, value, MIN_DIMENSIONS[axis], too_large=False))

    if problems:
        return SizeResult(height, width, depth, category=None, out_of_range=tuple(problems))

    # The largest category required by any single dimension wins.
    index = max(_category_index_for(axis, value) for axis, value in values.items())
    return SizeResult(height, width, depth, category=CATEGORIES[index])


def color_surcharge(is_custom: bool) -> int:
    return CUSTOM_COLOR_SURCHARGE if is_custom else 0


def total_price(base_price: int | None, is_custom_color: bool) -> int | None:
    """Total_Price = Category_Base_Price + (30 EUR if custom colour else 0). None if manual calculation."""
    if base_price is None:
        return None
    return base_price + color_surcharge(is_custom_color)
