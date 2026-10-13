import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# PostgreSQL: либо полный DATABASE_URL, либо отдельные POSTGRES_* переменные
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "ladada")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_DB = os.getenv("POSTGRES_DB", "ladada_bot")

# Google Sheets (service account JSON). Если не заданы — запись в таблицу отключена.
GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
GOOGLE_SHEETS_CREDENTIALS_PATH = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")
GOOGLE_SHEETS_WORKSHEET = os.getenv("GOOGLE_SHEETS_WORKSHEET", "Заявки")

# Т‑Банк интернет-эквайринг
TBANK_TERMINAL_KEY = os.getenv("TBANK_TERMINAL_KEY", "")
TBANK_PASSWORD = os.getenv("TBANK_PASSWORD", "")
TBANK_API_URL = os.getenv("TBANK_API_URL", "https://securepay.tinkoff.ru/v2").rstrip("/")
TBANK_NOTIFICATION_URL = os.getenv("TBANK_NOTIFICATION_URL", "")
TBANK_SUCCESS_URL = os.getenv("TBANK_SUCCESS_URL", "")
TBANK_FAIL_URL = os.getenv("TBANK_FAIL_URL", "")
# Проверка SSL при запросах к API банка (false — только если корп. прокси подменяет сертификат)
TBANK_SSL_VERIFY = os.getenv("TBANK_SSL_VERIFY", "true").lower() in ("1", "true", "yes")

# HTTP-сервер для notification webhook (за nginx)
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "0.0.0.0")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))

# Прокси только для Telegram Bot API (socks5:// или http://). Пусто = без прокси.
TELEGRAM_PROXY_URL = os.getenv("TELEGRAM_PROXY_URL", "") or None


def get_postgres_connect_kwargs() -> dict:
    """Параметры подключения Peewee к PostgreSQL."""
    if DATABASE_URL:
        return {"database": DATABASE_URL}
    return {
        "database": POSTGRES_DB,
        "user": POSTGRES_USER,
        "password": POSTGRES_PASSWORD,
        "host": POSTGRES_HOST,
        "port": POSTGRES_PORT,
    }
