#!/usr/bin/env python3
"""
Перенос данных из старой SQLite-базы (ladada_bot.db) в PostgreSQL.

Использование:
  1. Настройте POSTGRES_* или DATABASE_URL в .env
  2. Убедитесь, что PostgreSQL запущен и база создана
  3. python scripts/migrate_sqlite_to_postgres.py [путь_к_sqlite.db]

По умолчанию ищет ladada_bot.db в корне проекта.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from peewee import SqliteDatabase

from database.models import (
    MockExamApplication,
    PaymentApplication,
    SpeakingClubApplication,
    TrialApplication,
    User,
    db,
    init_db,
)

TABLES = (
    User,
    TrialApplication,
    PaymentApplication,
    SpeakingClubApplication,
    MockExamApplication,
)

_SEQUENCE_TABLES = (
    "trial_applications",
    "payment_applications",
    "speaking_club_applications",
    "mock_exam_applications",
)


def _read_sqlite_rows(sqlite_db: SqliteDatabase, model) -> list[dict]:
    orig_db = model._meta.database
    sqlite_db.bind([model], bind_refs=False, bind_backrefs=False)
    try:
        return list(model.select().dicts())
    finally:
        orig_db.bind([model], bind_refs=False, bind_backrefs=False)


def _reset_sequences() -> None:
    for table in _SEQUENCE_TABLES:
        db.execute_sql(
            f"""
            SELECT setval(
                pg_get_serial_sequence('{table}', 'id'),
                COALESCE((SELECT MAX(id) FROM {table}), 1)
            )
            """
        )


def migrate(sqlite_path: Path) -> None:
    if not sqlite_path.is_file():
        raise SystemExit(f"Файл SQLite не найден: {sqlite_path}")

    sqlite_db = SqliteDatabase(str(sqlite_path))
    sqlite_db.connect()
    print(f"Источник: {sqlite_path}")
    print("Цель: PostgreSQL (из .env)")

    init_db()

    for model in TABLES:
        rows = _read_sqlite_rows(sqlite_db, model)
        if not rows:
            print(f"  {model._meta.table_name}: 0 строк — пропуск")
            continue

        with db.atomic():
            for row in rows:
                if model is User:
                    User.insert(**row).on_conflict(
                        conflict_target=[User.user_id],
                        preserve=(User.username, User.first_name, User.last_name, User.updated_at),
                    ).execute()
                else:
                    model.insert(**row).on_conflict_ignore().execute()

        print(f"  {model._meta.table_name}: перенесено {len(rows)} строк")

    _reset_sequences()
    sqlite_db.close()
    db.close()
    print("Миграция завершена.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Перенос SQLite → PostgreSQL")
    parser.add_argument(
        "sqlite_path",
        nargs="?",
        default=ROOT / "ladada_bot.db",
        type=Path,
        help="Путь к файлу ladada_bot.db",
    )
    args = parser.parse_args()
    migrate(args.sqlite_path)


if __name__ == "__main__":
    main()
