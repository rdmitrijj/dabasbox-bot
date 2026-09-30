"""Entry point: python -m bot

On Render (RENDER_EXTERNAL_URL is set automatically) the bot runs in webhook mode:
it listens on $PORT and Telegram delivers updates to /webhook.
Everywhere else (e.g. your own computer) it runs in polling mode as before.
"""

from __future__ import annotations

import asyncio
import logging
import os
import secrets
import signal
import sys

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from pydantic import ValidationError

from .config import Settings, StorageBackend, get_settings
from .handlers import build_root_router
from .i18n import LANGUAGES, LanguageMiddleware
from .services.locks import UserLocks
from .services.orders import OrderLog

logger = logging.getLogger("dabasbox_bot")

WEBHOOK_PATH = "/webhook"


def build_storage(settings: Settings) -> BaseStorage:
    if settings.fsm_storage is StorageBackend.REDIS:
        from aiogram.fsm.storage.redis import RedisStorage  # requires the `redis` package

        return RedisStorage.from_url(
            settings.redis_url, state_ttl=settings.redis_state_ttl, data_ttl=settings.redis_state_ttl
        )
    return MemoryStorage()


def build_dispatcher(settings: Settings, storage: BaseStorage | None = None) -> Dispatcher:
    dp = Dispatcher(
        storage=storage or build_storage(settings),
        settings=settings,
        user_locks=UserLocks(),
        order_log=OrderLog(settings.orders_log_path),
    )
    language_middleware = LanguageMiddleware()
    dp.message.outer_middleware(language_middleware)
    dp.callback_query.outer_middleware(language_middleware)
    dp.include_router(build_root_router())
    return dp


def build_bot(settings: Settings) -> Bot:
    return Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


COMMAND_DESCRIPTIONS = {
    "en": {"start": "Start a new order", "cancel": "Cancel the current order", "language": "Change language", "help": "Help"},
    "lv": {"start": "Sākt jaunu pasūtījumu", "cancel": "Atcelt pasūtījumu", "language": "Mainīt valodu", "help": "Palīdzība"},
    "ru": {"start": "Новый заказ", "cancel": "Отменить заказ", "language": "Сменить язык", "help": "Помощь"},
}


async def set_commands(bot: Bot) -> None:
    """Command menu in the user's Telegram app language (English for everyone else)."""
    for code in LANGUAGES:
        commands = [BotCommand(command=c, description=d) for c, d in COMMAND_DESCRIPTIONS[code].items()]
        await bot.set_my_commands(commands, language_code=None if code == "en" else code)


async def health(_: web.Request) -> web.Response:
    """Simple page so Render (and you, in a browser) can see the service is up."""
    return web.Response(text="ok")


async def run_webhook(bot: Bot, dp: Dispatcher, base_url: str) -> None:
    # Telegram sends this secret with every update, so strangers can't post fake updates.
    secret = os.environ.get("WEBHOOK_SECRET") or secrets.token_urlsafe(32)
    port = int(os.environ.get("PORT", "10000"))

    app = web.Application()
    app.router.add_get("/", health)
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=secret).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, host="0.0.0.0", port=port).start()
    logger.info("Listening on port %s", port)

    webhook_url = f"{base_url.rstrip('/')}{WEBHOOK_PATH}"
    await bot.set_webhook(
        webhook_url,
        secret_token=secret,
        allowed_updates=dp.resolve_used_update_types(),
    )
    logger.info("Webhook set to %s", webhook_url)

    # Keep running until Render stops the service.
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)
    try:
        await stop.wait()
    finally:
        logger.info("Shutting down")
        await runner.cleanup()


async def main() -> None:
    try:
        settings = get_settings()
    except ValidationError as exc:
        print(f"Configuration error:\n{exc}\n\nSee .env.example.", file=sys.stderr)
        raise SystemExit(2) from exc

    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    base_url = os.environ.get("RENDER_EXTERNAL_URL")  # set automatically by Render
    mode = "webhook" if base_url else "polling"

    bot = build_bot(settings)
    dp = build_dispatcher(settings)
    try:
        me = await bot.get_me()
        logger.info(
            "Starting @%s, mode=%s, storage=%s, admin chat=%s",
            me.username, mode, settings.fsm_storage.value, settings.admin_chat_id,
        )
        await set_commands(bot)

        if base_url:
            await run_webhook(bot, dp, base_url)
        else:
            await bot.delete_webhook(drop_pending_updates=False)
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await dp.storage.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit) as exc:
        if isinstance(exc, SystemExit) and exc.code not in (None, 0):
            raise