"""Клиент API интернет-эквайринга Т‑Банка (Init + проверка Token уведомлений)."""
from __future__ import annotations

import hashlib
import logging
import ssl
import sys
from typing import Any, Mapping, MutableMapping, Optional, Union

import aiohttp
import certifi

import config

logger = logging.getLogger(__name__)

# Вложенные объекты не участвуют в подписи Token
_SKIP_TOKEN_KEYS = frozenset({"Token", "Receipt", "DATA", "Data"})

_tbank_session: Optional[aiohttp.ClientSession] = None
_truststore_injected = False


def _inject_truststore() -> None:
    global _truststore_injected
    if _truststore_injected:
        return
    import truststore

    truststore.inject_into_ssl()
    _truststore_injected = True


def _tbank_ssl_param() -> Union[bool, ssl.SSLContext]:
    """
    SSL для securepay.tinkoff.ru.
    Сертификат банка подписан Russian Trusted Root CA — на macOS его часто нет,
    на Linux VPS в РФ обычно есть в системном хранилище.
    """
    if not config.TBANK_SSL_VERIFY:
        logger.warning("TBANK_SSL_VERIFY=false — проверка сертификата банка отключена")
        return False

    if config.TBANK_CA_BUNDLE:
        return ssl.create_default_context(cafile=config.TBANK_CA_BUNDLE)

    use_system = config.TBANK_SSL_USE_SYSTEM and sys.platform.startswith("linux")
    if use_system:
        try:
            _inject_truststore()
            return ssl.create_default_context()
        except Exception as e:
            logger.warning("truststore недоступен, fallback на certifi: %s", e)

    return ssl.create_default_context(cafile=certifi.where())


def _tbank_connector() -> aiohttp.TCPConnector:
    return aiohttp.TCPConnector(ssl=_tbank_ssl_param())


async def get_tbank_session() -> aiohttp.ClientSession:
    """Переиспользуемая сессия для Init (без прокси — только прямой выход к банку)."""
    global _tbank_session
    if _tbank_session is None or _tbank_session.closed:
        _tbank_session = aiohttp.ClientSession(connector=_tbank_connector())
    return _tbank_session


async def close_tbank_session() -> None:
    global _tbank_session
    if _tbank_session is not None and not _tbank_session.closed:
        await _tbank_session.close()
    _tbank_session = None


def generate_token(payload: Mapping[str, Any], password: str) -> str:
    """
    Подпись запроса/уведомления Т‑Банка:
    плоские поля (без Token и вложенных объектов) + Password,
    сортировка по ключу, конкатенация значений, SHA-256.
    """
    data: dict[str, Any] = {
        key: value
        for key, value in payload.items()
        if key not in _SKIP_TOKEN_KEYS and not isinstance(value, (dict, list))
    }
    data["Password"] = password
    concatenated = "".join(str(data[key]) for key in sorted(data.keys()))
    return hashlib.sha256(concatenated.encode("utf-8")).hexdigest()


def verify_notification(payload: Mapping[str, Any], password: Optional[str] = None) -> bool:
    password = password if password is not None else config.TBANK_PASSWORD
    if not password:
        logger.error("TBANK_PASSWORD не задан — невозможно проверить уведомление")
        return False
    received = payload.get("Token")
    if not received:
        return False
    expected = generate_token(payload, password)
    return received == expected


class TBankError(Exception):
    def __init__(self, message: str, *, error_code: str = "", details: str = ""):
        super().__init__(message)
        self.error_code = error_code
        self.details = details


async def init_payment(
    *,
    amount_rub: int,
    order_id: str,
    description: str,
    customer_key: Optional[str] = None,
    session: Optional[aiohttp.ClientSession] = None,
) -> dict[str, Any]:
    """
    Инициализация платежа (POST /Init).
    Amount передаётся в копейках. Возвращает сырой JSON ответа банка.
    """
    if not config.TBANK_TERMINAL_KEY or not config.TBANK_PASSWORD:
        raise TBankError("Не заданы TBANK_TERMINAL_KEY / TBANK_PASSWORD")

    body: MutableMapping[str, Any] = {
        "TerminalKey": config.TBANK_TERMINAL_KEY,
        "Amount": int(amount_rub) * 100,
        "OrderId": order_id,
        "Description": description[:140],
        "PayType": "O",
    }
    if config.TBANK_NOTIFICATION_URL:
        body["NotificationURL"] = config.TBANK_NOTIFICATION_URL
    if config.TBANK_SUCCESS_URL:
        body["SuccessURL"] = config.TBANK_SUCCESS_URL
    if config.TBANK_FAIL_URL:
        body["FailURL"] = config.TBANK_FAIL_URL
    if customer_key is not None:
        body["CustomerKey"] = str(customer_key)

    body["Token"] = generate_token(body, config.TBANK_PASSWORD)
    url = f"{config.TBANK_API_URL}/Init"

    owns_session = session is None
    if owns_session:
        session = await get_tbank_session()

    try:
        assert session is not None
        async with session.post(url, json=dict(body), timeout=aiohttp.ClientTimeout(total=30)) as resp:
            data = await resp.json(content_type=None)
    except aiohttp.ClientConnectorCertificateError as e:
        logger.error(
            "SSL к Т‑Банку не прошёл. Установите certifi или задайте TBANK_SSL_VERIFY=false "
            "если трафик идёт через корпоративный прокси с подменой сертификата: %s",
            e,
        )
        raise TBankError(
            "Не удалось установить защищённое соединение с платёжным сервисом. "
            "Проверьте интернет или обратитесь к администратору."
        ) from e
    except Exception as e:
        logger.exception("Ошибка запроса Init к Т‑Банку: %s", e)
        raise TBankError(f"Сеть/ответ Init: {e}") from e

    if not data.get("Success"):
        raise TBankError(
            data.get("Message") or "Init неуспешен",
            error_code=str(data.get("ErrorCode") or ""),
            details=str(data.get("Details") or ""),
        )

    if not data.get("PaymentURL") or data.get("PaymentId") is None:
        raise TBankError("Init без PaymentURL/PaymentId", details=str(data))

    return data
