# Ladada English Bot

Telegram-бот для школы английского языка Ladada English.

## Технологии

- **Python 3.12+**
- **aiogram 3.x** - асинхронный фреймворк для Telegram Bot API
- **PostgreSQL** - база данных
- **peewee** + **psycopg2** - ORM и драйвер PostgreSQL
- **python-dotenv** - для работы с переменными окружения

## Установка

1. Убедитесь, что у вас установлен Python 3.12 или выше
2. Установите и запустите PostgreSQL (локально или на сервере)
3. Создайте базу и пользователя, например:

```sql
CREATE USER ladada WITH PASSWORD 'your_password';
CREATE DATABASE ladada_bot OWNER ladada;
```

4. Установите зависимости:

```bash
pip install -r requirements.txt
```

5. Скопируйте `.env.example` в `.env` и заполните переменные:

```bash
cp .env.example .env
```

Минимум для БД — `POSTGRES_*` или `DATABASE_URL`:

```env
BOT_TOKEN=your_bot_token_here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=ladada
POSTGRES_PASSWORD=your_password
POSTGRES_DB=ladada_bot
```

6. Получите токен бота у [@BotFather](https://t.me/BotFather) в Telegram

## Запуск

```bash
python main.py
```

При первом запуске таблицы создаются автоматически (`init_db`).

Бот поднимает polling Telegram и HTTP-сервер для уведомлений Т‑Банка (`WEBHOOK_PORT`, по умолчанию 8080).

Оплата, деплой, один сервер с VK-ботом и чеклист заказчика: см. [DEPLOY.md](DEPLOY.md).

### Миграция со старой SQLite-базы

Если есть файл `ladada_bot.db` от предыдущей версии:

```bash
python scripts/migrate_sqlite_to_postgres.py
# или с явным путём:
python scripts/migrate_sqlite_to_postgres.py /path/to/ladada_bot.db
```

## Структура проекта

```
LadadaEnglishBot/
├── main.py                 # Точка входа, запуск бота
├── config.py              # Конфигурация (токен, настройки БД)
├── requirements.txt       # Зависимости проекта
├── database/
│   ├── __init__.py
│   └── models.py          # Модели PostgreSQL (User, заявки, платежи)
├── scripts/
│   └── migrate_sqlite_to_postgres.py
└── handlers/
    ├── __init__.py
    └── start.py           # Обработчик команды /start
```

## Функционал

### Команда /start
При отправке команды `/start` бот:
- Сохраняет/обновляет информацию о пользователе в базе данных
- Отправляет приветственное сообщение с описанием возможностей
- Предоставляет 5 интерактивных кнопок:
  1. Записаться на бесплатное пробное занятие
  2. Узнать о школе, занятиях и активностях
  3. Купить курс «плати за 2, получай 7»
  4. Посмотреть отзывы
  5. Скачать бесплатные материалы

## База данных

PostgreSQL. Таблицы: `users`, `trial_applications`, `payment_applications`, `speaking_club_applications`, `mock_exam_applications`.

Схема создаётся автоматически при старте бота. Для переноса данных из SQLite см. раздел «Миграция» выше.

## Разработка

Для добавления новых обработчиков:
1. Создайте новый файл в папке `handlers/`
2. Создайте роутер и обработчики
3. Импортируйте роутер в `handlers/__init__.py`
4. Зарегистрируйте роутер в `main.py`
