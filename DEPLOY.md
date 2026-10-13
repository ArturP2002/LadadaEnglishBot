# Деплой: Т‑Банк, один сервер для TG + VK

## Что запросить у заказчика

### Т‑Банк / бизнес
- Подключённый интернет-эквайринг и интернет-магазин в ЛК Т‑Бизнес
- `TerminalKey` и пароль терминала (тестовый + боевой)
- Решение по онлайн-кассе 54‑ФЗ (касса + связка с эквайрингом; в коде `Receipt` пока не передаём)
- В ЛК терминала: Notification URL, Success URL, Fail URL

### Инфраструктура
- VPS в РФ: SSH (host, user, ключ/пароль), sudo
- **PostgreSQL** (локально на VPS или managed)
- Домен + DNS A-запись на сервер (HTTPS обязателен для уведомлений банка)
- Возможность поставить nginx + certbot (или готовый SSL)
- Прокси с доступом к `api.telegram.org` (тип HTTP/SOCKS5, host, port, login/password) — **только для Telegram-бота**
- Токен Telegram-бота (уже есть)

## Переменные `.env` (Telegram-бот)

```env
# PostgreSQL
DATABASE_URL=postgresql://ladada:password@localhost:5432/ladada_bot
# или POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB

TBANK_TERMINAL_KEY=...
TBANK_PASSWORD=...
TBANK_API_URL=https://securepay.tinkoff.ru/v2
TBANK_NOTIFICATION_URL=https://pay.example.com/tbank/notification
TBANK_SUCCESS_URL=https://pay.example.com/success
TBANK_FAIL_URL=https://pay.example.com/fail
TBANK_SSL_VERIFY=true
WEBHOOK_HOST=127.0.0.1
WEBHOOK_PORT=8080
TELEGRAM_PROXY_URL=socks5://user:pass@proxy-host:1080
```

`TELEGRAM_PROXY_URL` можно оставить пустым на машине, где Telegram API доступен напрямую.

### PostgreSQL на сервере

```bash
sudo apt install postgresql
sudo -u postgres psql -c "CREATE USER ladada WITH PASSWORD '...';"
sudo -u postgres psql -c "CREATE DATABASE ladada_bot OWNER ladada;"
```

Таблицы создаются при первом запуске бота. Перенос из старой SQLite: `python scripts/migrate_sqlite_to_postgres.py`.

### SSL к API Т‑Банка

Сертификат `securepay.tinkoff.ru` подписан **Russian Trusted Root CA**.

| Окружение | Настройка |
|---|---|
| VPS в РФ (prod) | `TBANK_SSL_VERIFY=true` — на Linux используется системное хранилище CA |
| macOS / локально | часто нужно `TBANK_SSL_VERIFY=false`, иначе `CERTIFICATE_VERIFY_FAILED` |
| Корп. прокси | `TBANK_SSL_VERIFY=false` или `TBANK_CA_BUNDLE=/path/to/ca.pem` |

## Один сервер: TG + VK

Да, оба бота на одном VPS.

1. Каталоги: `/opt/ladada-tg`, `/opt/ladada-vk` (отдельные venv, `.env`; общая или отдельная PostgreSQL).
2. Systemd: `ladada-tg.service`, `ladada-vk.service` с `Restart=always`.
3. Порты не пересекать: TG webhook `127.0.0.1:8080`; VK Callback — другой порт или другой `location` в nginx.
4. Nginx + Let’s Encrypt на домене (например `pay.example.com`):
   - `/tbank/notification` → `http://127.0.0.1:8080`
   - `/success`, `/fail` → тот же upstream
5. `TELEGRAM_PROXY_URL` только в unit/env **Telegram**-бота. ВК без зарубежного прокси.
6. Логи: `journalctl -u ladada-tg -f`, `journalctl -u ladada-vk -f`.

### Пример nginx

```nginx
server {
    listen 443 ssl http2;
    server_name pay.example.com;

    # ssl_certificate / ssl_certificate_key — certbot

    location /tbank/notification {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    location /success { proxy_pass http://127.0.0.1:8080; }
    location /fail    { proxy_pass http://127.0.0.1:8080; }
}
```

### Пример systemd (Telegram)

```ini
[Unit]
Description=Ladada English Telegram Bot
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/ladada-tg
EnvironmentFile=/opt/ladada-tg/.env
ExecStart=/opt/ladada-tg/.venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Мощность сервера

Оба бота — I/O-bound (polling/longpoll + редкие платежи/CRM).

| | Рекомендация |
|---|---|
| Старт | **2 vCPU, 2 GB RAM, 20–40 GB SSD** |
| Запас | 2 vCPU / 4 GB при росте медиа |

Узкое место чаще качество прокси до Telegram, не CPU.

## Прокси (только Telegram)

- Через прокси: сессия aiogram → `api.telegram.org`
- **Без** прокси: Init Т‑Банка, AmoCRM, Google Sheets, входящий webhook банка
- Задаётся `TELEGRAM_PROXY_URL` в `.env`; пустое значение = прямое подключение

## Проверка после деплоя

1. `curl -I https://pay.example.com/success` → 200
2. Тестовый терминал: кнопка «Оплатить» в боте → ссылка Т‑Банка
3. Оплата тестовой картой → сообщение в боте + сделка в AmoCRM
4. В логах банка Notification без ошибок (ответ `OK`)
