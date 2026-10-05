"""End-to-end tests: feed real Telegram updates through the dispatcher with a fake Bot API session."""

from __future__ import annotations

import itertools
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.methods import SendMediaGroup, SendMessage, SendPhoto, TelegramMethod
from aiogram.types import (
    CallbackQuery,
    Chat,
    Contact,
    InlineKeyboardMarkup,
    Message,
    PhotoSize,
    Update,
    User,
)

from bot.__main__ import build_dispatcher
from bot.config import Settings

ADMIN_CHAT_ID = -1001234567890


class FakeEmailChecker:
    """No real DNS in tests: every domain accepts mail except the ones listed here."""

    NO_MAIL = {"nomail.lv"}

    async def accepts_mail(self, domain: str) -> bool:
        return domain not in self.NO_MAIL


class FakeSession(BaseSession):
    def __init__(self) -> None:
        super().__init__()
        self.requests: list[TelegramMethod[Any]] = []
        self._ids = itertools.count(1000)

    def _message(self, chat_id: int, text: str | None = None) -> Message:
        return Message(
            message_id=next(self._ids),
            date=datetime.now(timezone.utc),
            chat=Chat(id=chat_id, type="private" if chat_id > 0 else "supergroup"),
            text=text,
        )

    async def make_request(self, bot: Bot, method: TelegramMethod[Any], timeout: int | None = None) -> Any:
        self.requests.append(method)
        if isinstance(method, SendMessage):
            return self._message(int(method.chat_id), method.text)
        if isinstance(method, SendPhoto):
            return self._message(int(method.chat_id))
        if isinstance(method, SendMediaGroup):
            return [self._message(int(method.chat_id)) for _ in method.media]
        return True

    async def stream_content(self, *args: Any, **kwargs: Any):  # pragma: no cover
        raise NotImplementedError
        yield b""

    async def close(self) -> None:
        pass

    def sent_to(self, chat_id: int) -> list[TelegramMethod[Any]]:
        return [r for r in self.requests if getattr(r, "chat_id", None) == chat_id]


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    log_path = tmp_path_factory.mktemp("data") / "orders.jsonl"
    settings = Settings(bot_token="42:TEST", admin_chat_id=ADMIN_CHAT_ID, orders_log_path=str(log_path))
    session = FakeSession()
    bot = Bot(token="42:TEST", session=session)
    dp = build_dispatcher(settings)  # routers are singletons: one dispatcher per test module
    dp["email_checker"] = FakeEmailChecker()
    return bot, dp, session, log_path


_update_ids = itertools.count(1)


class Customer:
    def __init__(self, env, user_id: int, username: str | None = "customer", lang: str = "en") -> None:
        self.bot, self.dp, self.session, self.log_path = env
        self.lang = lang
        self.lang_chosen = False
        self.user = User(id=user_id, is_bot=False, first_name="Test", username=username)
        self.chat = Chat(id=user_id, type="private")

    def _msg(self, **kwargs) -> Message:
        return Message(
            message_id=next(_update_ids), date=datetime.now(timezone.utc), chat=self.chat, from_user=self.user, **kwargs
        )

    async def send(self, **kwargs) -> None:
        await self.dp.feed_update(self.bot, Update(update_id=next(_update_ids), message=self._msg(**kwargs)))

    async def start(self) -> None:
        """/start; on the first visit the bot asks for a language, which we pick."""
        await self.text("/start")
        if not self.lang_chosen:
            await self.press(f"lang:{self.lang}")
            self.lang_chosen = True

    async def text(self, text: str) -> None:
        await self.send(text=text)

    async def photo(self, n: int) -> None:
        await self.send(photo=[PhotoSize(file_id=f"small{n}", file_unique_id=f"s{n}", width=90, height=90),
                               PhotoSize(file_id=f"photo{n}", file_unique_id=f"u{n}", width=1280, height=960)])

    async def press(self, data: str) -> None:
        cq = CallbackQuery(
            id=str(next(_update_ids)), from_user=self.user, chat_instance="ci", data=data, message=self._msg(text="kb")
        )
        await self.dp.feed_update(self.bot, Update(update_id=next(_update_ids), callback_query=cq))

    async def contact_and_payment(
        self, email: str = "john@example.com", phone: str = "+37120000000", name: str = "John", payment: str = "cash"
    ) -> None:
        await self.text(email)
        await self.text(phone)
        await self.text(name)
        await self.press(f"pay:{payment}")

    async def state(self) -> str | None:
        return await self.dp.fsm.get_context(self.bot, self.chat.id, self.user.id).get_state()

    def last_text(self) -> str:
        msgs = [r for r in self.session.sent_to(self.chat.id) if isinstance(r, SendMessage)]
        return msgs[-1].text

    def last_markup(self) -> InlineKeyboardMarkup | None:
        msgs = [r for r in self.session.sent_to(self.chat.id) if isinstance(r, SendMessage)]
        return msgs[-1].reply_markup

    def button_texts(self) -> list[str]:
        markup = self.last_markup()
        assert isinstance(markup, InlineKeyboardMarkup)
        return [b.text for row in markup.inline_keyboard for b in row]


async def test_full_order_base_color(env):
    c = Customer(env, 111)
    session = c.session

    await c.start()
    assert await c.state() == "OrderFSM:waiting_for_instruction_ack"
    assert c.button_texts() == ["Proceed to Enter Dimensions ➡️"]

    await c.press("nav:proceed_dimensions")
    assert await c.state() == "OrderFSM:waiting_for_dimensions"
    assert "NET actual dimensions" in c.last_text()

    await c.text("80x950x470")
    assert "couldn't read" in c.last_text()
    await c.text("750x900x450")
    assert await c.state() == "OrderFSM:waiting_for_photos"
    dims_msg = [r.text for r in session.sent_to(111) if isinstance(r, SendMessage)][-2]
    assert "Size category: <b>M</b>" in dims_msg and "280 €" in dims_msg

    # Done is not offered before the first photo; pressing a stale Done is refused.
    await c.press("nav:photos_done")
    assert await c.state() == "OrderFSM:waiting_for_photos"

    await c.photo(1)
    assert c.button_texts() == ["✅ Done, Continue", "🔄 Reset Photos"]
    await c.press("nav:photos_reset")
    await c.photo(2)
    await c.photo(3)
    await c.photo(4)
    await c.photo(5)  # 4th photo: rejected
    assert "Only 3 photos" in c.last_text()
    await c.press("nav:photos_done")
    assert await c.state() == "OrderFSM:waiting_for_color"

    await c.press("color:ral7016")
    assert await c.state() == "OrderFSM:waiting_for_country"
    await c.press("country:lv")
    assert await c.state() == "OrderFSM:waiting_for_address"

    await c.text("Riga")
    assert "too short" in c.last_text()
    await c.text("LV-1010, Riga, Brivibas iela 1-5")
    assert await c.state() == "OrderFSM:waiting_for_email"

    await c.text("john@example")
    assert "valid e-mail" in c.last_text()
    await c.text("john@gmail.co")
    assert "Did you mean <b>john@gmail.com</b>?" in c.last_text()
    await c.text("john@nomail.lv")
    assert "<b>nomail.lv</b> can't receive e-mail" in c.last_text()
    assert await c.state() == "OrderFSM:waiting_for_email"
    await c.text("john@Example.com")
    assert await c.state() == "OrderFSM:waiting_for_phone"
    await c.text("call me")
    assert "phone number is not valid" in c.last_text()
    await c.text("+371 2000 0000")
    assert await c.state() == "OrderFSM:waiting_for_name"
    await c.text("J0hn")
    assert "letters, hyphens" in c.last_text()
    await c.text("John")
    assert await c.state() == "OrderFSM:waiting_for_payment"
    assert c.button_texts() == ["💵 Cash", "🏦 Bank transfer"]
    await c.text("cash")
    assert "payment method" in c.last_text()
    await c.press("pay:transfer")
    assert await c.state() == "OrderFSM:waiting_for_confirmation"
    # The customer sees the photos that will be sent, right before the summary text.
    album, summary_msg = c.session.sent_to(c.chat.id)[-2:]
    assert isinstance(album, SendMediaGroup) and isinstance(summary_msg, SendMessage)
    assert [m.media for m in album.media] == ["photo2", "photo3", "photo4"]
    assert album.media[0].caption.startswith("🖼 <b>Your photos (3 pcs)</b>")
    summary = c.last_text()
    assert "<b>Name:</b> John" in summary
    assert "<b>E-mail:</b> john@example.com" in summary
    assert "<b>Payment:</b> 🏦 Bank transfer" in summary
    assert "M (Base price: 280 €)" in summary
    assert "The shipping cost will be sent to the specified e-mail address: john@example.com" in summary
    assert "Anthracite RAL7016 (0 €, included)" in summary
    assert "280 € (excl. 21% VAT)" in summary
    assert "LV-1010, Riga, Brivibas iela 1-5" in summary
    assert c.button_texts() == ["✅ Confirm & Submit Order", "❌ Cancel"]

    await c.press("nav:confirm")
    assert await c.state() is None
    assert "has been submitted" in c.last_text()

    admin = session.sent_to(ADMIN_CHAT_ID)
    assert isinstance(admin[0], SendMessage)
    card = admin[0].text
    assert card.startswith("📦 <b>NEW ORDER #DABASBOX-")
    assert "👤 Customer: John\n" in card
    assert "📧 Email: john@example.com" in card
    assert "📞 Phone: +37120000000" in card
    assert "💳 Payment: Bank transfer" in card
    assert "🏠 Postal Code &amp; Address: LV-1010, Riga, Brivibas iela 1-5" in card
    assert "750 mm (H) x 900 mm (W) x 450 mm (D)" in card
    assert "TOTAL PRICE: 280 € (excl. 21% VAT)" in card
    assert "Photos attached below (3 pcs)" in card
    assert isinstance(admin[1], SendMediaGroup)
    assert [m.media for m in admin[1].media] == ["photo2", "photo3", "photo4"]

    # Double tap after submission does not create a second order.
    n_admin = len(admin)
    await c.press("nav:confirm")
    assert len(session.sent_to(ADMIN_CHAT_ID)) == n_admin

    record = json.loads(c.log_path.read_text().strip().splitlines()[-1])
    assert record["status"] == "submitted" and record["total_price"] == 280
    assert record["email"] == "john@example.com" and record["payment"] == "transfer"


async def test_custom_color_other_country_shared_contact_manual_price(env):
    c = Customer(env, 222, username=None)
    await c.start()
    await c.press("nav:proceed_dimensions")
    await c.text("1700x1000x500")
    assert "Individual Manager Calculation" in c.last_text() or any(
        "Individual Manager Calculation" in (r.text or "") for r in c.session.sent_to(222) if isinstance(r, SendMessage)
    )
    assert await c.state() == "OrderFSM:waiting_for_photos"
    await c.photo(1)
    await c.press("nav:photos_done")
    await c.press("color:custom")
    assert await c.state() == "OrderFSM:waiting_for_custom_color_code"
    await c.text("RAL 90")
    assert "valid RAL" in c.last_text()
    await c.text("ral 9005")
    await c.press("country:other")
    assert await c.state() == "OrderFSM:waiting_for_country"
    await c.text("Poland")
    await c.text("00-950 Warszawa, ul. Marszalkowska 10")
    await c.text("anna@example.pl")
    await c.send(contact=Contact(phone_number="48600100200", first_name="Anna", user_id=222))
    assert await c.state() == "OrderFSM:waiting_for_name"
    await c.text("Anna")
    await c.press("pay:cash")
    assert await c.state() == "OrderFSM:waiting_for_confirmation"
    photo = c.session.sent_to(c.chat.id)[-2]
    assert isinstance(photo, SendPhoto) and photo.caption.startswith("🖼 <b>Your photos (1 pcs)</b>")
    summary = c.last_text()
    assert "Individual Manager Calculation" in summary
    assert "TO BE CALCULATED BY A MANAGER (+30 € custom colour surcharge applies)" in summary
    assert "Custom: RAL 9005 (+30 €)" in summary

    await c.press("nav:confirm")
    admin = c.session.sent_to(ADMIN_CHAT_ID)
    card = admin[-2].text
    assert "Customer: Anna" in card and "+48600100200" in card and "Payment: Cash" in card
    assert "Height 1700 mm is above the maximum of 1600 mm" in card
    assert "tg://user?id=222" in card
    assert isinstance(admin[-1], SendPhoto)


async def test_cancel_and_html_escaping(env):
    c = Customer(env, 333)
    await c.start()
    await c.press("nav:proceed_dimensions")
    await c.text("800x950x470")
    await c.photo(1)
    await c.press("nav:photos_done")
    await c.press("color:custom")
    await c.text("Blue <b>")
    assert "RAL/NCS code" in c.last_text()
    await c.text("/cancel")
    assert await c.state() is None
    assert "cancelled" in c.last_text()
    await c.press("nav:confirm")  # stale button from the old flow
    await c.text("hello")
    assert "/start" in c.last_text()


async def test_wrong_input_type_hints(env):
    c = Customer(env, 444)
    await c.start()
    await c.press("nav:proceed_dimensions")
    await c.photo(1)
    assert "dimensions as text" in c.last_text()
    await c.text("1000x1000x500")
    await c.text("some text")
    assert "Please send 1–3 photos" in c.last_text()


async def test_admin_failure_keeps_order_for_retry(env, monkeypatch):
    from aiogram.exceptions import TelegramNetworkError

    c = Customer(env, 555)
    await c.start()
    await c.press("nav:proceed_dimensions")
    await c.text("1000x1000x500")
    await c.photo(1)
    await c.press("nav:photos_done")
    await c.press("color:rr32")
    await c.press("country:ee")
    await c.text("10111 Tallinn, Narva mnt 5")
    await c.contact_and_payment(email="mari@example.ee", phone="+37250000000", name="Mari")
    assert await c.state() == "OrderFSM:waiting_for_confirmation"

    original = c.session.make_request

    async def failing(bot, method, timeout=None):
        if getattr(method, "chat_id", None) == ADMIN_CHAT_ID:
            raise TelegramNetworkError(method=method, message="down")
        return await original(bot, method, timeout)

    monkeypatch.setattr(c.session, "make_request", failing)
    await c.press("nav:confirm")
    assert await c.state() == "OrderFSM:waiting_for_confirmation"
    assert "couldn't submit" in c.last_text()

    monkeypatch.setattr(c.session, "make_request", original)
    await c.press("nav:confirm")
    assert await c.state() is None
    assert "L (Base price: 320 €)" in c.session.sent_to(ADMIN_CHAT_ID)[-2].text


async def test_step_images_are_sent_as_photos(env, tmp_path, monkeypatch):
    from bot import media

    (tmp_path / "start.png").write_bytes(b"\x89PNG fake")
    (tmp_path / "color.jpg").write_bytes(b"fake jpg")
    monkeypatch.setattr(media, "IMAGES_DIR", tmp_path)

    c = Customer(env, 666)
    await c.start()
    start_photo = [r for r in c.session.sent_to(666) if isinstance(r, SendPhoto)][-1]
    assert "Welcome to Dabasbox" in start_photo.caption

    await c.press("nav:proceed_dimensions")
    assert "NET actual dimensions" in c.last_text()  # no dimensions image: plain text
    await c.text("800x950x470")
    await c.photo(1)
    await c.press("nav:photos_done")
    color_photo = [r for r in c.session.sent_to(666) if isinstance(r, SendPhoto)][-1]
    assert color_photo.caption == "🎨 Please choose the enclosure colour:"
    assert isinstance(color_photo.reply_markup, InlineKeyboardMarkup)
    await c.press("color:rr32")
    assert await c.state() == "OrderFSM:waiting_for_country"


async def test_language_variant_replaces_step_image(env, tmp_path, monkeypatch):
    from bot import media

    folder = tmp_path / "dimensions"
    folder.mkdir()
    for name in ("dimensions.png", "pumpinfo.png", "pumpinfo.lv.png"):
        (folder / name).write_bytes(b"fake")
    monkeypatch.setattr(media, "IMAGES_DIR", tmp_path)

    for user_id, lang, expected in ((901, "en", "pumpinfo.png"), (902, "lv", "pumpinfo.lv.png")):
        c = Customer(env, user_id, lang=lang)
        await c.start()
        await c.press("nav:proceed_dimensions")
        album = [r for r in c.session.sent_to(user_id) if isinstance(r, SendMediaGroup)][-1]
        assert [Path(m.media.path).name for m in album.media] == ["dimensions.png", expected]


async def test_long_text_goes_after_the_photo(env, tmp_path, monkeypatch):
    from bot import media

    (tmp_path / "start.png").write_bytes(b"fake")
    monkeypatch.setattr(media, "IMAGES_DIR", tmp_path)
    from bot.locales import en

    monkeypatch.setitem(en.TEXTS, "welcome", "x" * 1100)

    c = Customer(env, 777)
    await c.start()
    sent = c.session.sent_to(777)
    photo_index = next(i for i, r in enumerate(sent) if isinstance(r, SendPhoto))
    assert sent[photo_index].caption is None
    assert sent[photo_index + 1].text == "x" * 1100


async def test_first_start_asks_for_language_then_runs_in_latvian(env):
    c = Customer(env, 888, lang="lv")
    await c.text("/start")
    assert "Choose your language" in c.last_text()
    assert await c.state() is None
    await c.press("lang:lv")
    c.lang_chosen = True
    assert await c.state() == "OrderFSM:waiting_for_instruction_ack"
    assert c.button_texts() == ["Ievadīt izmērus ➡️"]

    await c.press("nav:proceed_dimensions")
    assert "NETO izmērus" in c.last_text()
    await c.text("abc")
    assert "Neizdevās nolasīt izmērus" in c.last_text()
    await c.text("750x900x450")
    await c.photo(1)
    await c.press("nav:photos_done")
    assert c.button_texts() == ["Antracīts RAL7016 (0€)", "Tumši brūns RR32 (0€)", "Cita RAL / NCS krāsa (+30€)"]
    await c.press("color:ral7016")
    await c.press("country:other")
    await c.text("Latvija")  # typed in Latvian still maps to Latvia (LV postal code rules)
    await c.text("Rīga, Brīvības iela 1")
    assert "pasta indeksu (Latvija)" in c.last_text()
    await c.text("LV-1010, Rīga, Brīvības iela 1")
    await c.text("janis@example.lv")
    await c.text("+37120000000")
    await c.text("Jānis")
    assert c.button_texts() == ["💵 Skaidrā naudā", "🏦 Ar bankas pārskaitījumu"]
    await c.press("pay:cash")
    summary = c.last_text()
    assert "💳 <b>Apmaksa:</b> 💵 Skaidrā naudā" in summary
    assert "PASŪTĪJUMA KOPSAVILKUMS" in summary
    assert "Antracīts RAL7016 (0 €, iekļauts)" in summary
    assert "🌍 <b>Valsts:</b> Latvija" in summary
    assert "280 € (bez 21% PVN)" in summary

    await c.press("nav:confirm")
    card = c.session.sent_to(ADMIN_CHAT_ID)[-2].text
    assert "🌍 Country: Latvia" in card  # admin card stays in English
    assert "Anthracite RAL7016" in card
    assert "🗣 Language: Latvian" in card
    assert "💳 Payment: Cash" in card  # stored as a key, shown in English

    # The language is remembered: the next /start goes straight to the order.
    await c.text("/start")
    assert await c.state() == "OrderFSM:waiting_for_instruction_ack"


async def test_change_language_mid_order(env):
    c = Customer(env, 999)
    await c.start()
    await c.press("nav:proceed_dimensions")
    await c.text("/language")
    await c.press("lang:ru")
    assert await c.state() == "OrderFSM:waiting_for_dimensions"
    assert "отправьте размеры текстом" in c.last_text()
    await c.text("1")
    assert "Не удалось распознать размеры" in c.last_text()
