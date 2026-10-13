"""
Добавление строк с заявками в Google Таблицу (service account + gspread).
Строка собирается в потоке обработчика бота (до asyncio.gather), чтобы не трогать БД из воркера.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime
from threading import Lock
from typing import List, Optional, Union

import gspread
from google.oauth2.service_account import Credentials

import config
from database.models import (
    MockExamApplication,
    PaymentApplication,
    SpeakingClubApplication,
    TrialApplication,
)

logger = logging.getLogger(__name__)

_SCOPES = ("https://www.googleapis.com/auth/spreadsheets",)

# Заголовки первой строки (создаются один раз, если лист пустой)
_SHEET_HEADERS: List[str] = [
    "Время",
    "Тип заявки",
    "ID в БД",
    "Telegram ID",
    "Username",
    "Имя",
    "Фамилия",
    "Период",
    "Сумма (RUB)",
    "Заметки",
]

# Внутренние коды из handlers → подпись в колонке B
_KIND_LABEL_RU: dict[str, str] = {
    "trial": "Пробное занятие",
    "payment": "Оплата курса",
    "speaking_club": "Спикинг-клаб",
    "mock_exam": "Пробник с экспертами",
}

_client: Optional[gspread.Client] = None
_worksheet: Optional[gspread.Worksheet] = None
_client_lock = Lock()
_header_checked = False


def google_sheets_enabled() -> bool:
    return bool(config.GOOGLE_SHEETS_SPREADSHEET_ID and config.GOOGLE_SHEETS_CREDENTIALS_PATH)


def _get_worksheet() -> Optional[gspread.Worksheet]:
    global _client, _worksheet, _header_checked

    if not google_sheets_enabled():
        return None

    with _client_lock:
        if _worksheet is not None:
            return _worksheet

        cred_path = config.GOOGLE_SHEETS_CREDENTIALS_PATH
        if not cred_path or not os.path.isfile(cred_path):
            logger.error("Google Sheets: файл ключа не найден: %s", cred_path)
            return None

        try:
            creds = Credentials.from_service_account_file(cred_path, scopes=_SCOPES)
            _client = gspread.authorize(creds)
            sh = _client.open_by_key(config.GOOGLE_SHEETS_SPREADSHEET_ID)
            _worksheet = sh.worksheet(config.GOOGLE_SHEETS_WORKSHEET)
        except Exception as e:
            logger.error("Google Sheets: не удалось открыть таблицу: %s", e, exc_info=True)
            _client = None
            _worksheet = None
            return None

        if not _header_checked:
            _ensure_header_row(_worksheet)
            _header_checked = True

        return _worksheet


def _ensure_header_row(ws: gspread.Worksheet) -> None:
    try:
        existing = ws.get_values("A1:J1")
        if existing and existing[0] and any(cell.strip() for cell in existing[0]):
            return
        ws.update("A1:J1", [_SHEET_HEADERS], value_input_option="USER_ENTERED")
    except Exception as e:
        logger.warning("Google Sheets: не удалось проверить/создать заголовок: %s", e)


def _append_row_sync(row: List[str]) -> None:
    ws = _get_worksheet()
    if ws is None:
        return
    with _client_lock:
        ws.append_row(row, value_input_option="USER_ENTERED")


async def append_sheet_row_async(row: List[str]) -> None:
    """Добавить строку в таблицу (синхронный gspread — в thread pool)."""
    if not google_sheets_enabled():
        return
    await asyncio.to_thread(_append_row_sync, row)


def build_row_for_application(
    application: Union[
        TrialApplication,
        PaymentApplication,
        SpeakingClubApplication,
        MockExamApplication,
    ],
    kind: str,
) -> List[str]:
    """
    Собрать строку для листа. Вызывать в том же потоке, где создана заявка (до gather с CRM).
    kind (внутренний код): trial | payment | speaking_club | mock_exam → в таблице подпись на русском.
    """
    user = application.user
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    type_ru = _KIND_LABEL_RU.get(kind, kind)

    period = ""
    amount = ""
    notes = application.notes or ""

    if isinstance(application, PaymentApplication):
        period = "2 недели" if application.period == "2_weeks" else "1 месяц"
        amount = str(application.amount)

    row: List[str] = [
        now,
        type_ru,
        str(application.id),
        str(user.user_id),
        user.username or "",
        user.first_name or "",
        user.last_name or "",
        period,
        amount,
        notes,
    ]
    return row
