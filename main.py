import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

import config
from database.models import close_db, init_db
from handlers import start_router
from payments.service import handle_tbank_notification, set_bot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

SUCCESS_HTML = """<!DOCTYPE html>
<html lang="ru">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Оплата прошла</title></head>
<body style="font-family:system-ui,sans-serif;max-width:28rem;margin:3rem auto;padding:0 1rem;text-align:center">
<h1>Оплата прошла успешно</h1>
<p>Можешь вернуться в Telegram-бот — подтверждение придёт туда автоматически.</p>
</body></html>
"""

FAIL_HTML = """<!DOCTYPE html>
<html lang="ru">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Оплата не прошла</title></head>
<body style="font-family:system-ui,sans-serif;max-width:28rem;margin:3rem auto;padding:0 1rem;text-align:center">
<h1>Оплата не завершена</h1>
<p>Попробуй ещё раз из бота или напиши менеджеру @ladadada_boss.</p>
</body></html>
"""


async def tbank_notification_handler(request: web.Request) -> web.Response:
    """POST /tbank/notification — уведомления Т‑Банка."""
    try:
        payload = await request.json()
    except Exception:
        logger.warning("Т‑Банк notification: невалидный JSON")
        return web.Response(text="OK", content_type="text/plain")

    from payments.tbank import verify_notification

    if not verify_notification(payload):
        logger.warning("Т‑Банк notification: неверный Token, OrderId=%s", payload.get("OrderId"))
        return web.Response(status=403, text="Invalid token")

    # Тяжёлую логику (CRM, Telegram) — в фоне, ответ банку сразу OK (~10 с таймаут)
    asyncio.create_task(_process_tbank_notification(payload))
    return web.Response(text="OK", content_type="text/plain")


async def _process_tbank_notification(payload: dict) -> None:
    try:
        await handle_tbank_notification(payload)
    except Exception:
        logger.exception("Ошибка обработки notification OrderId=%s", payload.get("OrderId"))


async def success_page(_request: web.Request) -> web.Response:
    return web.Response(text=SUCCESS_HTML, content_type="text/html")


async def fail_page(_request: web.Request) -> web.Response:
    return web.Response(text=FAIL_HTML, content_type="text/html")


def create_http_app() -> web.Application:
    app = web.Application()
    app.router.add_post("/tbank/notification", tbank_notification_handler)
    app.router.add_get("/success", success_page)
    app.router.add_get("/fail", fail_page)
    return app


async def main():
    """Основная функция запуска бота + HTTP webhook Т‑Банка"""
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN не найден! Убедитесь, что файл .env содержит BOT_TOKEN")
        return

    logger.info("Инициализация базы данных...")
    init_db()
    logger.info("База данных инициализирована")

    session = None
    if config.TELEGRAM_PROXY_URL:
        logger.info("Telegram API через прокси")
        session = AiohttpSession(proxy=config.TELEGRAM_PROXY_URL)

    bot = Bot(token=config.BOT_TOKEN, session=session)
    set_bot(bot)
    dp = Dispatcher()
    dp.include_router(start_router)

    http_app = create_http_app()
    runner = web.AppRunner(http_app)
    await runner.setup()
    site = web.TCPSite(runner, config.WEBHOOK_HOST, config.WEBHOOK_PORT)
    await site.start()
    logger.info(
        "HTTP webhook слушает %s:%s (/tbank/notification, /success, /fail)",
        config.WEBHOOK_HOST,
        config.WEBHOOK_PORT,
    )
    logger.info("Бот запущен и готов к работе!")

    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        await bot.session.close()
        from payments.tbank import close_tbank_session
        await close_tbank_session()
        close_db()


if __name__ == "__main__":
    asyncio.run(main())
