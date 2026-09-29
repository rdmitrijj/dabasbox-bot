"""Commands available in any state (/start, /cancel, /language, /help), plus global fallbacks."""

from __future__ import annotations

from contextlib import suppress

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import BaseStorage
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from .. import keyboards as kb
from ..i18n import CHOOSE_LANGUAGE, LANGUAGES, Translator, save_language
from ..media import send_step
from ..states import OrderFSM
from .order import STATE_HINTS

router = Router(name="common")
router.message.filter(F.chat.type == "private")
router.callback_query.filter(F.message.chat.type == "private")

fallback_router = Router(name="fallback")
fallback_router.message.filter(F.chat.type == "private")


async def start_order(message: Message, state: FSMContext, t: Translator) -> None:
    await state.clear()
    await state.set_state(OrderFSM.waiting_for_instruction_ack)
    await send_step(message, "start", t("welcome"), ReplyKeyboardRemove())
    await message.answer(t("tap_when_measured"), reply_markup=kb.instruction_ack_kb(t))


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, t: Translator, lang_chosen: bool) -> None:
    if not lang_chosen:
        # First visit: ask for the language, the order starts once it's picked.
        await state.clear()
        await message.answer(CHOOSE_LANGUAGE, reply_markup=kb.language_kb())
        return
    await start_order(message, state, t)


@router.message(Command("language"))
async def cmd_language(message: Message) -> None:
    await message.answer(CHOOSE_LANGUAGE, reply_markup=kb.language_kb())


@router.callback_query(kb.LangCb.filter())
async def on_language(
    callback: CallbackQuery, callback_data: kb.LangCb, state: FSMContext, bot: Bot, fsm_storage: BaseStorage
) -> None:
    if callback_data.code not in LANGUAGES:
        await callback.answer()
        return
    await save_language(fsm_storage, bot.id, callback.from_user.id, callback_data.code)
    t = Translator(callback_data.code)
    await callback.answer(t("language_set"))
    if not isinstance(callback.message, Message):
        return
    with suppress(TelegramBadRequest):
        await callback.message.edit_text(t("language_set"))

    if await state.get_state() is None:
        await start_order(callback.message, state, t)  # nothing in progress: begin the order
    else:
        # Mid-order: remind them of the current step in the new language.
        await callback.message.answer(t(STATE_HINTS.get(await state.get_state() or "", "use_start")))


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, t: Translator) -> None:
    if await state.get_state() is None:
        await message.answer(t("nothing_to_cancel"), reply_markup=ReplyKeyboardRemove())
        return
    await state.clear()
    await message.answer(t("cancelled"), reply_markup=ReplyKeyboardRemove())


@router.message(Command("help"))
async def cmd_help(message: Message, t: Translator) -> None:
    await message.answer(t("help"))


@fallback_router.message(StateFilter(None))
async def no_active_order(message: Message, t: Translator) -> None:
    await message.answer(t("use_start"))


# Registered on the dispatcher last: any button that no handler accepted is from an old message.
stale_callback_router = Router(name="stale_callbacks")


@stale_callback_router.callback_query()
async def stale_callback(callback: CallbackQuery, t: Translator) -> None:
    await callback.answer(t("stale_button"), show_alert=False)
