"""Step-by-step order flow handlers (OrderFSM)."""

from __future__ import annotations

import logging
from contextlib import suppress
from dataclasses import replace

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from .. import keyboards as kb
from ..catalog import BASE_COLORS, COUNTRIES, PAYMENT_METHODS
from ..config import Settings
from ..i18n import LANGUAGES, Translator
from ..media import send_step
from ..order import IncompleteOrderError, Order
from ..pricing import CUSTOM_COLOR_SURCHARGE, classify
from ..services.email_domains import EmailDomainChecker
from ..services.locks import UserLocks
from ..services.orders import OrderLog, generate_order_id, notify_admins
from ..states import OrderFSM
from ..utils import escape
from ..validators import (
    ValidationError,
    normalize_phone,
    parse_address,
    parse_country,
    parse_custom_color,
    parse_dimensions,
    parse_email,
    parse_first_name,
)

logger = logging.getLogger(__name__)
router = Router(name="order")
# The order flow only runs in private chats (the admin group must never trigger it).
router.message.filter(F.chat.type == "private")
router.callback_query.filter(F.message.chat.type == "private")

MAX_PHOTOS = 3


async def _error(message: Message, t: Translator, exc: ValidationError) -> None:
    params = {key: escape(value) for key, value in exc.params.items()}
    if "country" in exc.params:
        params["country"] = escape(t.country(str(exc.params["country"])))
    await message.answer(f"❌ {t(exc.key, **params)}")


async def _drop_markup(callback: CallbackQuery) -> None:
    """Remove the inline keyboard from the message the button belonged to (ignore if impossible)."""
    if isinstance(callback.message, Message):
        with suppress(TelegramBadRequest):
            await callback.message.edit_reply_markup(reply_markup=None)


async def _restart_required(message: Message, state: FSMContext, t: Translator) -> None:
    await state.clear()
    await message.answer(t("restart_required"), reply_markup=ReplyKeyboardRemove())


# ============================================================ Step 1 -> 2: instructions ack

@router.callback_query(OrderFSM.waiting_for_instruction_ack, kb.NavCb.filter(F.action == "proceed_dimensions"))
async def on_instructions_ack(callback: CallbackQuery, state: FSMContext, t: Translator) -> None:
    await callback.answer()
    await _drop_markup(callback)
    await state.set_state(OrderFSM.waiting_for_dimensions)
    if isinstance(callback.message, Message):
        await send_step(callback.message, "dimensions", t("ask_dimensions"), lang=t.lang)


# ============================================================ Step 2: dimensions

@router.message(OrderFSM.waiting_for_dimensions, F.text)
async def on_dimensions(message: Message, state: FSMContext, t: Translator) -> None:
    try:
        dims = parse_dimensions(message.text or "")
    except ValidationError as exc:
        await _error(message, t, exc)
        return

    result = classify(dims.height, dims.width, dims.depth)
    await state.update_data(
        height=result.height,
        width=result.width,
        depth=result.depth,
        category=result.category.code if result.category else None,
        out_of_range=[p.describe() for p in result.out_of_range],
        photos=[],
        photo_status_msg_id=None,
    )

    dims_line = t("dims_line", h=result.height, w=result.width, d=result.depth)
    if result.needs_manual_calculation:
        problems = "\n".join(
            "• "
            + t(
                "out_above" if p.too_large else "out_below",
                axis=t(f"axis_{p.axis.value}"),
                value=p.value,
                limit=p.limit,
            )
            for p in result.out_of_range
        )
        await message.answer(dims_line + "\n\n" + t("manual_notice", problems=problems))
    else:
        assert result.category is not None
        await message.answer(
            dims_line + "\n" + t("dims_category", category=result.category.code, price=result.category.base_price)
        )

    await state.set_state(OrderFSM.waiting_for_photos)
    await send_step(message, "photos", t("ask_photos"), lang=t.lang)


# ============================================================ Step 3: photos

async def _send_photo_status(
    message: Message, state: FSMContext, t: Translator, count: int, note: str = ""
) -> None:
    data = await state.get_data()
    old_id = data.get("photo_status_msg_id")
    if old_id:
        with suppress(TelegramAPIError):
            await message.bot.delete_message(message.chat.id, old_id)  # type: ignore[union-attr]
    hint = t("photos_more_hint") if count < MAX_PHOTOS else t("photos_max_hint")
    status = await message.answer(
        f"{note}{t('photos_status', count=count, max=MAX_PHOTOS)}\n{hint}", reply_markup=kb.photos_kb(t, count)
    )
    await state.update_data(photo_status_msg_id=status.message_id)


@router.message(OrderFSM.waiting_for_photos, F.photo)
async def on_photo(message: Message, state: FSMContext, user_locks: UserLocks, t: Translator) -> None:
    assert message.photo and message.from_user
    async with user_locks.hold(message.from_user.id):
        # Re-check: a concurrent album item may have moved the state on (e.g. user pressed Done).
        if await state.get_state() != OrderFSM.waiting_for_photos.state:
            return
        photos: list[str] = list((await state.get_data()).get("photos") or [])
        if len(photos) >= MAX_PHOTOS:
            await _send_photo_status(message, state, t, len(photos), note=t("photos_skipped", max=MAX_PHOTOS) + "\n")
            return
        photos.append(message.photo[-1].file_id)  # largest available resolution
        await state.update_data(photos=photos)
        await _send_photo_status(message, state, t, len(photos))


@router.message(OrderFSM.waiting_for_photos, F.document)
async def on_photo_as_document(message: Message, t: Translator) -> None:
    await message.answer(t("photo_as_document"))


@router.callback_query(OrderFSM.waiting_for_photos, kb.NavCb.filter(F.action == "photos_reset"))
async def on_photos_reset(callback: CallbackQuery, state: FSMContext, user_locks: UserLocks, t: Translator) -> None:
    async with user_locks.hold(callback.from_user.id):
        await state.update_data(photos=[])
        await callback.answer(t("photos_cleared"))
        if isinstance(callback.message, Message):
            with suppress(TelegramBadRequest):
                await callback.message.edit_text(
                    f"{t('photos_status', count=0, max=MAX_PHOTOS)}\n{t('ask_photos')}",
                    reply_markup=kb.photos_kb(t, 0),
                )
            await state.update_data(photo_status_msg_id=callback.message.message_id)


@router.callback_query(OrderFSM.waiting_for_photos, kb.NavCb.filter(F.action == "photos_done"))
async def on_photos_done(callback: CallbackQuery, state: FSMContext, user_locks: UserLocks, t: Translator) -> None:
    async with user_locks.hold(callback.from_user.id):
        photos = (await state.get_data()).get("photos") or []
        if not photos:
            await callback.answer(t("photos_need_one"), show_alert=True)
            return
        await callback.answer()
        await _drop_markup(callback)
        await state.update_data(photo_status_msg_id=None)
        await state.set_state(OrderFSM.waiting_for_color)
    if isinstance(callback.message, Message):
        await send_step(callback.message, "color", t("ask_color"), kb.color_kb(t), lang=t.lang)


# ============================================================ Step 4: colour

@router.callback_query(OrderFSM.waiting_for_color, kb.ColorCb.filter())
async def on_color(callback: CallbackQuery, callback_data: kb.ColorCb, state: FSMContext, t: Translator) -> None:
    if callback_data.key == "custom":
        await callback.answer()
        await _drop_markup(callback)
        await state.set_state(OrderFSM.waiting_for_custom_color_code)
        if isinstance(callback.message, Message):
            await send_step(callback.message, "custom_color", t("ask_custom_color"), lang=t.lang)
        return

    name = BASE_COLORS.get(callback_data.key)
    if name is None:
        await callback.answer(t("stale_button"), show_alert=True)
        return
    display = t(f"color_{callback_data.key}")
    await callback.answer(display)
    await _drop_markup(callback)
    await state.update_data(color_name=name, color_key=callback_data.key, custom_color=False, custom_color_code=None)
    await state.set_state(OrderFSM.waiting_for_country)
    if isinstance(callback.message, Message):
        await callback.message.answer(t("color_chosen", name=display, surcharge=t("surcharge_included")))
        await send_step(callback.message, "country", t("ask_country"), kb.country_kb(t), lang=t.lang)


@router.message(OrderFSM.waiting_for_custom_color_code, F.text)
async def on_custom_color(message: Message, state: FSMContext, t: Translator) -> None:
    try:
        code = parse_custom_color(message.text or "")
    except ValidationError as exc:
        await _error(message, t, exc)
        return
    await state.update_data(color_name=f"Custom: {code}", color_key="custom", custom_color=True, custom_color_code=code)
    await state.set_state(OrderFSM.waiting_for_country)
    await message.answer(
        t(
            "color_chosen",
            name=t("color_custom_name", code=escape(code)),
            surcharge=t("surcharge_custom", surcharge=CUSTOM_COLOR_SURCHARGE),
        )
    )
    await send_step(message, "country", t("ask_country"), kb.country_kb(t), lang=t.lang)


# ============================================================ Step 5: country

@router.callback_query(OrderFSM.waiting_for_country, kb.CountryCb.filter())
async def on_country(callback: CallbackQuery, callback_data: kb.CountryCb, state: FSMContext, t: Translator) -> None:
    await callback.answer()
    if callback_data.key == "other":
        await _drop_markup(callback)
        if isinstance(callback.message, Message):
            await callback.message.answer(t("ask_other_country"))
        return  # stay in waiting_for_country; the typed name is handled below

    country = COUNTRIES.get(callback_data.key)
    if country is None:
        return
    await _drop_markup(callback)
    await state.update_data(country=country)
    await state.set_state(OrderFSM.waiting_for_address)
    if isinstance(callback.message, Message):
        await send_step(
            callback.message, "address", f"{t('country_chosen', country=t.country(country))}\n\n{t('ask_address')}",
            lang=t.lang,
        )


@router.message(OrderFSM.waiting_for_country, F.text)
async def on_country_text(message: Message, state: FSMContext, t: Translator) -> None:
    try:
        country = parse_country(message.text or "")
    except ValidationError as exc:
        await _error(message, t, exc)
        return
    # Map typed Baltic countries (in any bot language) to the canonical names so postal code validation applies.
    canonical = {name.lower(): name for name in COUNTRIES.values()}
    for key, name in COUNTRIES.items():
        for module in LANGUAGES.values():
            canonical[module.TEXTS[f"country_{key}"].lower()] = name
    country = canonical.get(country.lower(), country)
    await state.update_data(country=country)
    await state.set_state(OrderFSM.waiting_for_address)
    await send_step(
        message, "address", f"{t('country_chosen', country=escape(t.country(country)))}\n\n{t('ask_address')}",
        lang=t.lang,
    )


# ============================================================ Step 6: address

@router.message(OrderFSM.waiting_for_address, F.text)
async def on_address(message: Message, state: FSMContext, t: Translator) -> None:
    country = (await state.get_data()).get("country")
    if not country:
        await _restart_required(message, state, t)
        return
    try:
        address = parse_address(message.text or "", country)
    except ValidationError as exc:
        await _error(message, t, exc)
        return
    await state.update_data(zip_code=address.zip_code, address=address.address)
    await state.set_state(OrderFSM.waiting_for_email)
    await message.answer(t("address_saved", zip=escape(address.zip_code), address=escape(address.address)))
    await send_step(message, "email", t("ask_email"), lang=t.lang)


# ============================================================ Step 7: e-mail, phone, first name

@router.message(OrderFSM.waiting_for_email, F.text)
async def on_email(message: Message, state: FSMContext, t: Translator, email_checker: EmailDomainChecker) -> None:
    try:
        email = parse_email(message.text or "")
        domain = email.rsplit("@", 1)[1]
        if not await email_checker.accepts_mail(domain):
            raise ValidationError("err_email_domain", domain=domain)
    except ValidationError as exc:
        await _error(message, t, exc)
        return
    await state.update_data(email=email)
    await state.set_state(OrderFSM.waiting_for_phone)
    await send_step(message, "phone", t("ask_phone"), kb.phone_kb(t), lang=t.lang)


async def _phone_entered(message: Message, state: FSMContext, t: Translator, raw: str) -> None:
    try:
        phone = normalize_phone(raw)
    except ValidationError as exc:
        await _error(message, t, exc)
        return
    await state.update_data(phone=phone)
    await state.set_state(OrderFSM.waiting_for_name)
    await send_step(message, "name", t("ask_name"), ReplyKeyboardRemove(), lang=t.lang)


@router.message(OrderFSM.waiting_for_phone, F.contact)
async def on_shared_contact(message: Message, state: FSMContext, t: Translator) -> None:
    assert message.contact is not None
    await _phone_entered(message, state, t, message.contact.phone_number)


@router.message(OrderFSM.waiting_for_phone, F.text)
async def on_phone_text(message: Message, state: FSMContext, t: Translator) -> None:
    await _phone_entered(message, state, t, message.text or "")


@router.message(OrderFSM.waiting_for_name, F.text)
async def on_name(message: Message, state: FSMContext, t: Translator) -> None:
    try:
        first_name = parse_first_name(message.text or "")
    except ValidationError as exc:
        await _error(message, t, exc)
        return
    await state.update_data(first_name=first_name)
    await state.set_state(OrderFSM.waiting_for_payment)
    await send_step(message, "payment", t("ask_payment"), kb.payment_kb(t), lang=t.lang)


# ============================================================ Step 8: payment method

@router.callback_query(OrderFSM.waiting_for_payment, kb.PaymentCb.filter())
async def on_payment(callback: CallbackQuery, callback_data: kb.PaymentCb, state: FSMContext, t: Translator) -> None:
    await callback.answer()
    if callback_data.method not in PAYMENT_METHODS:
        return
    await _drop_markup(callback)
    await state.update_data(payment=callback_data.method)
    if isinstance(callback.message, Message):
        await callback.message.answer(t("payment_chosen", payment=t(f"payment_{callback_data.method}")))
        await _show_summary(callback.message, state, t)


# ============================================================ Step 9: summary & confirmation

async def _show_summary(message: Message, state: FSMContext, t: Translator) -> None:
    try:
        order = Order.from_fsm(await state.get_data())
    except IncompleteOrderError:
        logger.warning("Incomplete order data for chat %s", message.chat.id, exc_info=True)
        await _restart_required(message, state, t)
        return
    await state.set_state(OrderFSM.waiting_for_confirmation)
    await message.answer(order.summary_html(t), reply_markup=kb.confirmation_kb(t))


@router.callback_query(OrderFSM.waiting_for_confirmation, kb.NavCb.filter(F.action == "confirm"))
async def on_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    settings: Settings,
    user_locks: UserLocks,
    order_log: OrderLog,
    t: Translator,
) -> None:
    user = callback.from_user
    async with user_locks.hold(user.id):
        # A double tap queues a second call behind the lock; by then the order is submitted.
        if await state.get_state() != OrderFSM.waiting_for_confirmation.state:
            await callback.answer(t("already_submitted"))
            return
        try:
            order = Order.from_fsm(await state.get_data())
        except IncompleteOrderError:
            await callback.answer()
            if isinstance(callback.message, Message):
                await _restart_required(callback.message, state, t)
            else:
                await state.clear()
            return

        order = replace(
            order,
            order_id=generate_order_id(),
            telegram_user_id=user.id,
            telegram_username=user.username,
            language=t.lang,
        )
        try:
            await notify_admins(bot, settings.admin_chat_id, order)
        except TelegramAPIError:
            logger.exception("Failed to deliver order %s to admin chat", order.order_id)
            await _safe_log(order_log, order, "admin_notification_failed")
            await callback.answer(t("submit_failed_alert"), show_alert=True)
            if isinstance(callback.message, Message):
                await callback.message.answer(t("submit_failed"))
            return

        await _safe_log(order_log, order, "submitted")
        await state.clear()
        await callback.answer(t("order_submitted_alert"))
        await _drop_markup(callback)
        if isinstance(callback.message, Message):
            await callback.message.answer(t("order_submitted", order_id=escape(order.order_id or "")))
        logger.info("Order %s submitted by user %s", order.order_id, user.id)


async def _safe_log(order_log: OrderLog, order: Order, status: str) -> None:
    try:
        await order_log.append(order, status)
    except OSError:
        logger.exception("Could not write order %s to the local log", order.order_id)


@router.callback_query(OrderFSM.waiting_for_confirmation, kb.NavCb.filter(F.action == "cancel"))
async def on_cancel_button(callback: CallbackQuery, state: FSMContext, t: Translator) -> None:
    await state.clear()
    await callback.answer(t("order_cancelled_alert"))
    await _drop_markup(callback)
    if isinstance(callback.message, Message):
        await callback.message.answer(t("cancelled"))


# ============================================================ per-state fallbacks (wrong input type)

STATE_HINTS: dict[str, str] = {
    OrderFSM.waiting_for_instruction_ack.state: "hint_instruction_ack",
    OrderFSM.waiting_for_dimensions.state: "hint_dimensions",
    OrderFSM.waiting_for_photos.state: "hint_photos",
    OrderFSM.waiting_for_color.state: "hint_color",
    OrderFSM.waiting_for_custom_color_code.state: "hint_custom_color",
    OrderFSM.waiting_for_country.state: "hint_country",
    OrderFSM.waiting_for_address.state: "hint_address",
    OrderFSM.waiting_for_email.state: "hint_email",
    OrderFSM.waiting_for_phone.state: "hint_phone",
    OrderFSM.waiting_for_name.state: "hint_name",
    OrderFSM.waiting_for_payment.state: "hint_payment",
    OrderFSM.waiting_for_confirmation.state: "hint_confirmation",
}


@router.message(OrderFSM())
async def on_unexpected_input(message: Message, state: FSMContext, t: Translator) -> None:
    current = await state.get_state()
    await message.answer(t(STATE_HINTS.get(current or "", "use_start")))
