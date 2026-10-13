"""
Кэш Telegram file_id для локальных медиа.

Первая отправка заливает файл через FSInputFile и сохраняет file_id
(ключ = путь + mtime + size). Повторные отправки идут по file_id — без upload.
При смене файла на диске или невалидном file_id кэш сбрасывается и файл
заливается заново.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Sequence

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import (
    FSInputFile,
    InputMediaPhoto,
    Message,
)

logger = logging.getLogger(__name__)

# Рядом с корнем проекта (cwd при запуске бота)
_CACHE_PATH = Path("data/telegram_file_ids.json")
_lock = asyncio.Lock()
_memory: dict[str, dict[str, Any]] | None = None


def _norm_path(path: str | os.PathLike[str]) -> str:
    return os.path.normpath(str(path))


def _stat_meta(path: str) -> tuple[int, int] | None:
    try:
        st = os.stat(path)
    except OSError:
        return None
    return int(st.st_mtime_ns), int(st.st_size)


def _load_unlocked() -> dict[str, dict[str, Any]]:
    global _memory
    if _memory is not None:
        return _memory
    if _CACHE_PATH.exists():
        try:
            raw = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                _memory = {
                    str(k): v
                    for k, v in raw.items()
                    if isinstance(v, dict) and isinstance(v.get("file_id"), str)
                }
            else:
                _memory = {}
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Не удалось прочитать кэш file_id (%s): %s", _CACHE_PATH, e)
            _memory = {}
    else:
        _memory = {}
    return _memory


def _save_unlocked(data: dict[str, dict[str, Any]]) -> None:
    global _memory
    _memory = data
    try:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _CACHE_PATH.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        tmp.replace(_CACHE_PATH)
    except OSError as e:
        logger.warning("Не удалось сохранить кэш file_id (%s): %s", _CACHE_PATH, e)


def get_file_id(path: str | os.PathLike[str]) -> str | None:
    """Вернуть закэшированный file_id, если файл на диске не менялся."""
    key = _norm_path(path)
    meta = _stat_meta(key)
    if meta is None:
        return None
    mtime_ns, size = meta
    data = _load_unlocked()
    entry = data.get(key)
    if not entry:
        return None
    if entry.get("mtime_ns") == mtime_ns and entry.get("size") == size:
        return entry.get("file_id")
    return None


async def remember_file_id(path: str | os.PathLike[str], file_id: str) -> None:
    key = _norm_path(path)
    meta = _stat_meta(key)
    if meta is None or not file_id:
        return
    mtime_ns, size = meta
    async with _lock:
        data = dict(_load_unlocked())
        data[key] = {
            "file_id": file_id,
            "mtime_ns": mtime_ns,
            "size": size,
        }
        _save_unlocked(data)
    logger.debug("file_id закэширован: %s", key)


async def invalidate(path: str | os.PathLike[str]) -> None:
    key = _norm_path(path)
    async with _lock:
        data = dict(_load_unlocked())
        if key in data:
            del data[key]
            _save_unlocked(data)
            logger.info("file_id сброшен (невалидный или файл сменён): %s", key)


def media_input(
    path: str | os.PathLike[str],
    *,
    filename: str | None = None,
) -> str | FSInputFile:
    """file_id из кэша или FSInputFile для первой загрузки."""
    cached = get_file_id(path)
    if cached:
        return cached
    key = _norm_path(path)
    if filename:
        return FSInputFile(key, filename=filename)
    return FSInputFile(key)


def extract_file_id(message: Message) -> str | None:
    if message.video:
        return message.video.file_id
    if message.document:
        return message.document.file_id
    if message.animation:
        return message.animation.file_id
    if message.video_note:
        return message.video_note.file_id
    if message.audio:
        return message.audio.file_id
    if message.voice:
        return message.voice.file_id
    if message.photo:
        return message.photo[-1].file_id
    return None


def _is_bad_file_id_error(exc: BaseException) -> bool:
    text = str(exc).lower()
    needles = (
        "wrong file identifier",
        "file_id",
        "file identifier",
        "http url specified",
        "failed to get http url content",
    )
    return any(n in text for n in needles)


async def _send_with_cache(
    path: str,
    *,
    send_cached,
    send_upload,
    remember_from_message,
) -> Message:
    """Один раз попробовать file_id; при BadRequest — upload и кэш."""
    cached = get_file_id(path)
    if cached:
        try:
            return await send_cached(cached)
        except TelegramBadRequest as e:
            if not _is_bad_file_id_error(e):
                raise
            logger.warning("Невалидный file_id для %s, перезаливаем: %s", path, e)
            await invalidate(path)
        except TelegramForbiddenError:
            raise

    message = await send_upload()
    file_id = remember_from_message(message)
    if file_id:
        await remember_file_id(path, file_id)
    return message


async def send_video(
    bot: Bot,
    chat_id: int,
    path: str,
    **kwargs: Any,
) -> Message:
    async def _cached(file_id: str) -> Message:
        return await bot.send_video(chat_id=chat_id, video=file_id, **kwargs)

    async def _upload() -> Message:
        return await bot.send_video(
            chat_id=chat_id,
            video=FSInputFile(_norm_path(path)),
            **kwargs,
        )

    return await _send_with_cache(
        path,
        send_cached=_cached,
        send_upload=_upload,
        remember_from_message=extract_file_id,
    )


async def send_photo(
    bot: Bot,
    chat_id: int,
    path: str,
    **kwargs: Any,
) -> Message:
    async def _cached(file_id: str) -> Message:
        return await bot.send_photo(chat_id=chat_id, photo=file_id, **kwargs)

    async def _upload() -> Message:
        return await bot.send_photo(
            chat_id=chat_id,
            photo=FSInputFile(_norm_path(path)),
            **kwargs,
        )

    return await _send_with_cache(
        path,
        send_cached=_cached,
        send_upload=_upload,
        remember_from_message=extract_file_id,
    )


async def send_document(
    bot: Bot,
    chat_id: int,
    path: str,
    *,
    filename: str | None = None,
    **kwargs: Any,
) -> Message:
    name = filename or os.path.basename(path)

    async def _cached(file_id: str) -> Message:
        return await bot.send_document(chat_id=chat_id, document=file_id, **kwargs)

    async def _upload() -> Message:
        return await bot.send_document(
            chat_id=chat_id,
            document=FSInputFile(_norm_path(path), filename=name),
            **kwargs,
        )

    return await _send_with_cache(
        path,
        send_cached=_cached,
        send_upload=_upload,
        remember_from_message=extract_file_id,
    )


async def send_photo_album(
    bot: Bot,
    chat_id: int,
    paths: Sequence[str],
    *,
    caption: str | None = None,
    caption_entities: list | None = None,
    parse_mode: str | None = None,
) -> list[Message]:
    """
    Альбом фото с кэшем file_id по каждому пути.
    caption / caption_entities / parse_mode — только на первое фото.
    """
    if not paths:
        return []

    paths = [_norm_path(p) for p in paths]

    def _build_media(use_cache: bool) -> list[InputMediaPhoto]:
        media: list[InputMediaPhoto] = []
        for i, path in enumerate(paths):
            if use_cache:
                source: str | FSInputFile = media_input(path)
            else:
                source = FSInputFile(path)
            if i == 0 and (caption is not None or caption_entities is not None):
                media.append(
                    InputMediaPhoto(
                        media=source,
                        caption=caption,
                        caption_entities=caption_entities,
                        parse_mode=parse_mode,
                    )
                )
            else:
                media.append(InputMediaPhoto(media=source))
        return media

    async def _remember(messages: list[Message]) -> None:
        for path, msg in zip(paths, messages):
            file_id = extract_file_id(msg)
            if file_id:
                await remember_file_id(path, file_id)

    for use_cache in (True, False):
        try:
            messages = await bot.send_media_group(
                chat_id=chat_id,
                media=_build_media(use_cache=use_cache),
            )
            await _remember(messages)
            return messages
        except TelegramBadRequest as e:
            if use_cache and _is_bad_file_id_error(e):
                logger.warning("Невалидный file_id в альбоме, перезаливаем: %s", e)
                for p in paths:
                    await invalidate(p)
                continue
            raise

    return []  # unreachable; pacifies type checkers
