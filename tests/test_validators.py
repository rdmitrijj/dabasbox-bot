import pytest

from bot.validators import (
    ValidationError,
    normalize_phone,
    parse_address,
    parse_country,
    parse_custom_color,
    parse_dimensions,
    parse_email,
    parse_first_name,
)


@pytest.mark.parametrize(
    "text",
    ["800x950x470", "800 x 950 x 470", "800X950X470", "800х950х470", "800×950×470", "800,950,470", "800*950*470", "800x950x470 mm"],
)
def test_dimensions_ok(text):
    d = parse_dimensions(text)
    assert (d.height, d.width, d.depth) == (800, 950, 470)


@pytest.mark.parametrize("text", ["80x950x470", "800x950", "abc", "800x950x470x100", "0800x950x470", "80000x1x1", ""])
def test_dimensions_bad(text):
    with pytest.raises(ValidationError):
        parse_dimensions(text)


@pytest.mark.parametrize(
    ("text", "expected"),
    [("RAL 9005", "RAL 9005"), ("ral9005", "RAL 9005"), ("NCS S 1080-Y50R", "NCS S 1080-Y50R"), ("ncs s 0500-n", "NCS S 0500-N"), ("Moss green", "Moss green")],
)
def test_custom_color_ok(text, expected):
    assert parse_custom_color(text) == expected


@pytest.mark.parametrize("text", ["RAL 90", "NCS 12", "!!", "1234", "<b>x</b>"])
def test_custom_color_bad(text):
    with pytest.raises(ValidationError):
        parse_custom_color(text)


def test_country():
    assert parse_country("finland") == "Finland"
    assert parse_country("Czech Republic") == "Czech Republic"
    with pytest.raises(ValidationError):
        parse_country("12345")


def test_address_latvia():
    a = parse_address("LV-1010, Riga, Brivibas iela 1-5", "Latvia")
    assert a.zip_code == "LV-1010"
    assert a.address == "Riga, Brivibas iela 1-5"
    a = parse_address("Riga, Brivibas iela 12, LV 1050", "Latvia")
    assert a.zip_code == "LV-1050"


def test_address_lithuania_and_estonia():
    assert parse_address("LT-01103 Vilnius, Gedimino pr. 9", "Lithuania").zip_code == "LT-01103"
    assert parse_address("10111 Tallinn, Narva mnt 5", "Estonia").zip_code == "10111"


def test_address_other_country():
    a = parse_address("00-950 Warszawa, ul. Marszalkowska 10", "Poland")
    assert a.zip_code == "00-950"
    assert "Warszawa" in a.address


@pytest.mark.parametrize(
    ("text", "country"),
    [("Riga", "Latvia"), ("Brivibas iela, Riga", "Latvia"), ("12345 Vilnius street", "Latvia"), ("LV-1010", "Latvia")],
)
def test_address_bad(text, country):
    with pytest.raises(ValidationError):
        parse_address(text, country)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("+371 20 000 000", "+37120000000"), ("37120000000", "+37120000000"), ("00371-2000-0000", "+37120000000"), ("+1 (415) 555-2671", "+14155552671")],
)
def test_phone_ok(raw, expected):
    assert normalize_phone(raw) == expected


@pytest.mark.parametrize("raw", ["123", "+0123456789", "+1234567890123456", "phone"])
def test_phone_bad(raw):
    with pytest.raises(ValidationError):
        normalize_phone(raw)


@pytest.mark.parametrize(
    ("text", "expected"),
    [("john@example.com", "john@example.com"), (" John.Smith@Example.LV ", "John.Smith@example.lv"), ("a+b@mail.co.uk", "a+b@mail.co.uk")],
)
def test_email_ok(text, expected):
    assert parse_email(text) == expected


@pytest.mark.parametrize("text", ["john", "john@", "@example.com", "john@example", "john @example.com", "a@b@c.com", "john@example.c"])
def test_email_bad(text):
    with pytest.raises(ValidationError):
        parse_email(text)


@pytest.mark.parametrize(
    ("text", "suggestion"),
    [
        ("John@gmail.co", "John@gmail.com"),
        ("john@Gmail.Cm", "john@gmail.com"),
        ("john@gmial.com", "john@gmail.com"),
        ("john@gmail.lv", "john@gmail.com"),
        ("john@gmail.co.uk", "john@gmail.com"),
        ("john@inbox.lc", "john@inbox.lv"),
        ("john@inbx.lv", "john@inbox.lv"),
        ("john@hotmial.com", "john@hotmail.com"),
        ("john@hotmal.com", "john@hotmail.com"),
        ("john@otlok.com", "john@outlook.com"),
        ("john@outlok.com", "john@outlook.com"),
        ("john@mail.ry", "john@mail.ru"),
        ("john@icloud.lv", "john@icloud.com"),
    ],
)
def test_email_typo(text, suggestion):
    with pytest.raises(ValidationError) as exc:
        parse_email(text)
    assert exc.value.key == "err_email_typo"
    assert exc.value.params == {"suggestion": suggestion}


@pytest.mark.parametrize(
    "domain",
    ["gmail.com", "inbox.lv", "inbox.lt", "edu.riga.lv", "rtu.lv", "email.com", "ymail.com", "mail.de",
     "outlook.cz", "hotmail.de", "protonmail.ch", "fastmail.fm", "yandex.by", "company.lv"],
)
def test_email_not_typo(domain):
    assert parse_email(f"john@{domain}") == f"john@{domain}"


def test_first_name():
    assert parse_first_name("jānis") == "Jānis"
    assert parse_first_name(" Anna  Maria ") == "Anna Maria"
    assert parse_first_name("Mary-Jane") == "Mary-Jane"


@pytest.mark.parametrize("text", ["", "J0hn", "+37120000000", "a b c d"])
def test_first_name_bad(text):
    with pytest.raises(ValidationError):
        parse_first_name(text)
