import pytest

from bot.i18n import DEFAULT_LANGUAGE, LANGUAGES, Translator, placeholders


@pytest.mark.parametrize("code", [c for c in LANGUAGES if c != DEFAULT_LANGUAGE])
def test_locale_has_same_keys_and_placeholders(code):
    base = LANGUAGES[DEFAULT_LANGUAGE].TEXTS
    other = LANGUAGES[code].TEXTS
    assert set(other) == set(base)
    for key, text in base.items():
        assert placeholders(other[key]) == placeholders(text), key


@pytest.mark.parametrize("code", list(LANGUAGES))
def test_html_tags_balanced(code):
    for key, text in LANGUAGES[code].TEXTS.items():
        for tag in ("b", "code"):
            assert text.count(f"<{tag}>") == text.count(f"</{tag}>"), (code, key)


def test_translator_fallback_and_country():
    t = Translator("xx")
    assert t.lang == "en"
    assert Translator("ru").country("Latvia") == "Латвия"
    assert Translator("lv").country("Finland") == "Finland"
