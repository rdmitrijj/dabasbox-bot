# Dabasbox Order Bot

Telegram bot that takes orders for Dabasbox protective heat pump enclosures:
measurement instructions → net dimensions → 1–3 photos → colour → country → address → contact →
summary → confirmation → notification (with photos) to the managers' chat.

## How it looks like

![image alt](https://github.com/rdmitrijj/dabasbox-bot/blob/main/screenshot-2026-09-29_10.41.20.png?raw=true)



## Quick start

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in BOT_TOKEN and ADMIN_CHAT_ID
python -m bot
```

`ADMIN_CHAT_ID` is the chat that receives orders: a user id or a group id (`-100…`). Add the bot to the
group first. To find a group id, add e.g. @RawDataBot to the group temporarily, or read `chat.id` from
`https://api.telegram.org/bot<TOKEN>/getUpdates` after posting in the group.

### Docker (with Redis)

```bash
cp .env.example .env   # fill in BOT_TOKEN and ADMIN_CHAT_ID
docker compose up -d --build
```

The compose file switches FSM storage to Redis, so unfinished orders survive restarts.

## Configuration (.env)

| Variable | Default | Meaning |
| --- | --- | --- |
| `BOT_TOKEN` | required | Token from @BotFather |
| `ADMIN_CHAT_ID` | required | Management chat for new orders |
| `FSM_STORAGE` | `memory` | `memory` or `redis` |
| `REDIS_URL` | `redis://localhost:6379/0` | Used when `FSM_STORAGE=redis` |
| `REDIS_STATE_TTL` | `604800` | Seconds an unfinished order is kept in Redis |
| `ORDERS_LOG_PATH` | `data/orders.jsonl` | Every confirmed order is appended here as JSON |
| `LOG_LEVEL` | `INFO` | Python logging level |

## Business rules implemented

**Size category.** Each dimension is mapped to the smallest category whose upper bound covers it, and the
largest category across height, width and depth wins (e.g. 750×900×450 → M, 280 €). The catalogue ranges
overlap and have small gaps (width 871–879 mm sits between S and M); resolving to the smallest category whose
upper bound is not exceeded closes those gaps upwards, so the enclosure is never too small. Bounds are inclusive.

**Out of range.** Any dimension below the S minimum (680 / 720 / 420 mm) or above the XXL maximum
(1430 / 1320 / 820 mm) flags the order for **Individual Manager Calculation**: the user is told why, the flow
continues, and the summary and admin card show the price as "to be calculated by a manager" (plus the +30 €
note if a custom colour was chosen).

**Price.** `Total = base price + 30 € if custom RAL/NCS colour`, all excl. 21% VAT.

**Validation.**
- Dimensions: `H x W x D`, 3–4 digit integers; separators `x X х Х × , *`; a trailing `mm` is tolerated.
  (The regex in the brief had `\times` inside a character class, which Python reads as tab + letters; the
  intended `×` sign is used instead.)
- Photos: 1–3, sent as photos (files are refused with a hint). Albums are handled safely; extras beyond 3 are
  skipped with a notice. "Done, Continue" appears only after the first photo.
- Custom colour: RAL (`RAL 9005`, RAL Design `RAL 210 50 15`), NCS (`NCS S 1080-Y50R`), or a plain colour name.
- Address: 10–300 characters and must contain a postal code. Latvia `LV-####`, Lithuania `LT-#####`,
  Estonia `#####` are checked and normalised; other countries use a generic postal-code pattern. The postal
  code and the rest of the address are stored separately for the admin card.
- Contact: "Share Contact" button or text like `John Smith +37120000000`. Phones are normalised to E.164
  (`+`, 7–15 digits, no leading 0; `00` prefix converted to `+`). The brief's `^\+?\d{1,14}$` would accept
  1-digit numbers and reject valid 15-digit ones, so the E.164 length rule is used. If a shared contact has no
  last name, the bot asks for the full name.

**Robustness.**
- `/start` restarts, `/cancel` cancels at any step, `/language` switches language, `/help` lists commands.
- Wrong input type at any step gets a step-specific hint; buttons from old messages are answered as inactive.
- Per-user locks prevent lost photos in albums and duplicate orders on double-tapping Confirm.
- If the admin chat can't be reached, the customer is told and keeps the confirmation screen to retry;
  the attempt is logged. Telegram flood limits (`RetryAfter`) are retried automatically.
- The order flow only reacts in private chats, so the bot can sit in the admin group quietly.
- All user text is HTML-escaped.

The admin card follows the template in the brief, plus one `💬 Telegram:` line (username or a clickable user
link) so managers can message the customer directly. The order id looks like `DABASBOX-260928-A3F9`
(date + random suffix).

## Languages

The bot speaks English, Latvian and Russian. On the first /start the customer picks a language
(🇬🇧 / 🇱🇻 / 🇷🇺); it's remembered, and /language changes it at any time, even mid-order. The admin
card always stays in English and shows the customer's language.

All customer-facing texts live in `bot/locales/en.py`, `lv.py` and `ru.py` (one dictionary per language,
same keys). To change a text, edit it there. To add a language, copy `en.py` to e.g. `lt.py`, translate the
values, set `NAME`, and add it to `LANGUAGES` in `bot/i18n.py` (plus command descriptions in
`bot/__main__.py`). `tests/test_i18n.py` checks that every language has the same keys and `{placeholders}`.
The Latvian and Russian texts were machine-written; have a native speaker proofread them.

## Step images

To show a picture at a step, put an image file in `bot/images/` named after the step, e.g.
`bot/images/start.png` for the welcome message or `color.jpg` for the colour buttons. The step's text becomes
the photo caption (or follows the photo when it's longer than Telegram's 1024-character caption limit).
Names: `start`, `dimensions`, `photos`, `color`, `custom_color`, `country`, `address`, `contact`; extensions
`.jpg .jpeg .png .webp`. Steps without a file send plain text. See `bot/images/README.txt`.

## Project layout

```
bot/
  __main__.py        entry point, Bot/Dispatcher/storage wiring
  config.py          pydantic-settings configuration
  states.py          OrderFSM
  pricing.py         size matrix, category and price calculation
  validators.py      input parsing/validation (pure functions)
  catalog.py         base colours, countries
  keyboards.py       inline/reply keyboards and callback data
  i18n.py            languages, per-user language storage, translator middleware
  locales/           en.py, lv.py, ru.py — all customer-facing texts
  media.py           optional step images (bot/images/<step>.png)
  order.py           Order model, summary and admin notification formatting
  handlers/common.py /start, /cancel, /help, fallbacks
  handlers/order.py  step-by-step FSM handlers
  services/orders.py order id, JSONL log, admin notification
  services/locks.py  per-user locks
tests/               unit tests + end-to-end flow tests with a fake Bot API session
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The flow tests feed real Telegram `Update` objects through the dispatcher and assert on what the bot would
send, including the admin card and photo album.

## Scaling note

Per-user locks are in-process. Run one polling process per bot token (the normal setup); with Redis storage
the state survives restarts and redeploys.
