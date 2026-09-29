import pytest

from bot.pricing import classify, total_price


@pytest.mark.parametrize(
    ("dims", "expected"),
    [
        ((750, 900, 450), "M"),  # example from the specification
        ((700, 750, 430), "S"),
        ((780, 870, 480), "S"),  # S upper bounds inclusive
        ((781, 800, 430), "M"),
        ((700, 875, 430), "M"),  # width gap 871-879 resolves upwards to M
        ((800, 950, 470), "M"),
        ((700, 800, 510), "L"),  # depth alone pushes to L
        ((1000, 1000, 500), "L"),
        ((1200, 1000, 500), "XL"),
        ((700, 700 + 20, 700), "XXL"),  # depth 700 only fits XXL
        ((1430, 1320, 820), "XXL"),  # XXL upper bounds inclusive
        ((680, 720, 420), "S"),  # S lower bounds inclusive
    ],
)
def test_category(dims, expected):
    result = classify(*dims)
    assert result.category is not None
    assert result.category.code == expected


@pytest.mark.parametrize(
    "dims",
    [
        (1431, 1000, 500),
        (1000, 1321, 500),
        (1000, 1000, 821),
        (679, 800, 450),
        (700, 719, 450),
        (700, 800, 419),
    ],
)
def test_out_of_range_requires_manual_calculation(dims):
    result = classify(*dims)
    assert result.needs_manual_calculation
    assert result.base_price is None
    assert len(result.out_of_range) == 1


def test_multiple_out_of_range_reported():
    result = classify(2000, 500, 900)
    assert {p.axis.value for p in result.out_of_range} == {"height", "width", "depth"}


def test_total_price():
    assert total_price(280, False) == 280
    assert total_price(280, True) == 310
    assert total_price(None, True) is None
