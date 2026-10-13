"""Создание платежа и обработка webhook Т‑Банка."""
from __future__ import annotations

import logging
import secrets
import time
from datetime import datetime
from typing import Any, Mapping, Optional

from aiogram import Bot
from aiogram.utils.formatting import Bold, Text
from peewee import DoesNotExist

from database.models import PaymentApplication, User
from payments.catalog import PaymentProduct, get_product
from payments.tbank import TBankError, init_payment, verify_notification

logger = logging.getLogger(__name__)

_bot: Optional[Bot] = None

STATUS_PENDING = "PENDING"
STATUS_CONFIRMED = "CONFIRMED"
STATUS_REJECTED = "REJECTED"
STATUS_CANCELED = "CANCELED"
STATUS_REFUNDED = "REFUNDED"
STATUS_FAILED = "FAILED"

_TERMINAL_STATUSES = frozenset({
    STATUS_REJECTED,
    STATUS_CANCELED,
    STATUS_REFUNDED,
    "AUTH_FAIL",
    "DEADLINE_EXPIRED",
})


def set_bot(bot: Bot) -> None:
    global _bot
    _bot = bot


def get_bot() -> Optional[Bot]:
    return _bot


def _make_order_id(user_id: int) -> str:
    # Уникальный OrderId ≤ 50 символов
    return f"tg{user_id}t{int(time.time())}{secrets.token_hex(3)}"[:50]


async def create_payment_for_callback(
    *,
    user: User,
    callback_data: str,
) -> PaymentApplication:
    """Создаёт заказ в БД и инициирует платёж в Т‑Банке. CRM не трогает."""
    product = get_product(callback_data)
    if product is None:
        raise ValueError(f"Неизвестный продукт: {callback_data}")
    return await create_payment(user=user, product=product)


async def create_payment(
    *,
    user: User,
    product: PaymentProduct,
) -> PaymentApplication:
    order_id = _make_order_id(user.user_id)
    application = PaymentApplication.create(
        user=user,
        period=product.period,
        amount=product.amount_rub,
        notes=product.notes,
        order_id=order_id,
        status=STATUS_PENDING,
        course=product.course,
        created_at=datetime.now(),
    )

    try:
        data = await init_payment(
            amount_rub=product.amount_rub,
            order_id=order_id,
            description=product.description,
            customer_key=str(user.user_id),
        )
    except TBankError:
        application.status = STATUS_FAILED
        application.save()
        raise

    application.payment_id = str(data["PaymentId"])
    application.payment_url = data["PaymentURL"]
    application.status = str(data.get("Status") or STATUS_PENDING)
    application.save()
    logger.info(
        "Создан платёж order_id=%s payment_id=%s user=%s amount=%s",
        order_id,
        application.payment_id,
        user.user_id,
        product.amount_rub,
    )
    return application


def get_payment_link_message(amount_rub: int) -> Text:
    return Text(
        Bold("Ссылка на оплату готова"),
        "\n\n",
        f"Сумма: {amount_rub} ₽\n\n",
        "Нажми кнопку ниже, оплати на форме Т‑Банка и дождись подтверждения в этом чате.",
    )


def get_payment_success_message(amount_rub: int) -> Text:
    return Text(
        Bold("Yaaay, bestik, оплата прошла успешно"),
        "\n\n",
        f"Сумма: {amount_rub} ₽\n\n",
        "Совсем скоро наш менеджер напишет тебе с аккаунта @ladadada_boss\n\n",
        Bold("Проверь, пожалуйста, что личные сообщения открыты"),
        "\n\n",
        "А пока можешь погулять по боту — нажми «Домой».",
    )


async def handle_tbank_notification(payload: Mapping[str, Any]) -> None:
    """
    Обработка POST-уведомления банка (Token уже проверен в HTTP-слое или здесь).
    Идемпотентна по уже CONFIRMED заказам. CRM/Sheets — только после первой CONFIRMED.
    """
    if not verify_notification(payload):
        logger.warning("Уведомление Т‑Банка с неверной подписью Token: %s", payload.get("OrderId"))
        return

    order_id = payload.get("OrderId")
    status = str(payload.get("Status") or "")
    payment_id = payload.get("PaymentId")

    if not order_id:
        logger.warning("Уведомление без OrderId: %s", payload)
        return

    try:
        application = PaymentApplication.get(PaymentApplication.order_id == str(order_id))
    except DoesNotExist:
        logger.error("Заказ не найден для OrderId=%s", order_id)
        return

    if payment_id is not None and not application.payment_id:
        application.payment_id = str(payment_id)

    # Уже обработанная успешная оплата — идемпотентный выход
    if application.status == STATUS_CONFIRMED and application.paid_at:
        logger.info("Повтор CONFIRMED для order_id=%s — пропуск", order_id)
        return

    if status == STATUS_CONFIRMED:
        application.status = STATUS_CONFIRMED
        application.paid_at = datetime.now()
        application.save()
        await _on_payment_confirmed(application)
        return

    if status in _TERMINAL_STATUSES or status:
        # Обновляем промежуточные/финальные неуспешные статусы, не трогая CRM
        if application.status != STATUS_CONFIRMED:
            application.status = status
            application.save()
        logger.info("Статус платежа order_id=%s → %s", order_id, status)


async def _on_payment_confirmed(application: PaymentApplication) -> None:
    bot = _bot
    user = application.user

    if bot is not None:
        try:
            from handlers.keyboards import get_payment_confirmation_keyboard

            text = get_payment_success_message(application.amount)
            text_value, entities_value = text.render()
            await bot.send_message(
                chat_id=user.user_id,
                text=text_value,
                entities=entities_value,
                reply_markup=get_payment_confirmation_keyboard(),
                parse_mode=None,
            )
        except Exception as e:
            logger.exception("Не удалось отправить сообщение об оплате user=%s: %s", user.user_id, e)

    # Ленивый импорт — избегаем циклов handlers ↔ payments
    try:
        from handlers.start import send_payment_application_to_amo_crm, _parallel_crm_and_google_sheet
        from integrations.google_sheets import build_row_for_application

        row = build_row_for_application(application, "payment")
        await _parallel_crm_and_google_sheet(
            send_payment_application_to_amo_crm(application),
            row,
        )
    except Exception as e:
        logger.exception("CRM/Sheets после оплаты order_id=%s: %s", application.order_id, e)
