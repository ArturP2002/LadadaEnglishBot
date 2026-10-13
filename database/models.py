import logging
from datetime import datetime

from peewee import (
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    Model,
    TextField,
)
from playhouse.pool import PooledPostgresqlDatabase

import config

logger = logging.getLogger(__name__)

db = PooledPostgresqlDatabase(
    **config.get_postgres_connect_kwargs(),
    max_connections=20,
    stale_timeout=300,
)


class BaseModel(Model):
    """Базовая модель для всех таблиц"""

    class Meta:
        database = db


class User(BaseModel):
    """Модель пользователя"""

    user_id = IntegerField(unique=True, primary_key=True)
    username = CharField(null=True)
    first_name = CharField(null=True)
    last_name = CharField(null=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "users"

    def __str__(self):
        return f"User {self.user_id} ({self.username or self.first_name})"


class TrialApplication(BaseModel):
    """Модель заявки на пробное занятие"""

    user = ForeignKeyField(User, backref="trial_applications", on_delete="CASCADE")
    created_at = DateTimeField(default=datetime.now)
    sent_to_amo = BooleanField(default=False)
    amo_contact_id = CharField(null=True)
    notes = CharField(null=True)

    class Meta:
        table_name = "trial_applications"

    def __str__(self):
        return f"TrialApplication {self.id} from User {self.user.user_id}"


class PaymentApplication(BaseModel):
    """Модель заявки/заказа на оплату курса (в т.ч. через Т‑Банк)"""

    user = ForeignKeyField(User, backref="payment_applications", on_delete="CASCADE")
    period = CharField()
    amount = IntegerField()
    created_at = DateTimeField(default=datetime.now)
    sent_to_amo = BooleanField(default=False)
    amo_contact_id = CharField(null=True)
    amo_deal_id = CharField(null=True)
    notes = CharField(null=True)

    order_id = CharField(null=True, index=True)
    payment_id = CharField(null=True, index=True)
    status = CharField(default="PENDING")
    payment_url = TextField(null=True)
    paid_at = DateTimeField(null=True)
    course = CharField(null=True)

    class Meta:
        table_name = "payment_applications"

    def __str__(self):
        return f"PaymentApplication {self.id} from User {self.user.user_id} ({self.period})"


class SpeakingClubApplication(BaseModel):
    """Модель заявки на спикинг клаб"""

    user = ForeignKeyField(User, backref="speaking_club_applications", on_delete="CASCADE")
    created_at = DateTimeField(default=datetime.now)
    sent_to_amo = BooleanField(default=False)
    amo_contact_id = CharField(null=True)
    amo_deal_id = CharField(null=True)
    notes = CharField(null=True)

    class Meta:
        table_name = "speaking_club_applications"

    def __str__(self):
        return f"SpeakingClubApplication {self.id} from User {self.user.user_id}"


class MockExamApplication(BaseModel):
    """Модель заявки на пробник с экспертами"""

    user = ForeignKeyField(User, backref="mock_exam_applications", on_delete="CASCADE")
    created_at = DateTimeField(default=datetime.now)
    sent_to_amo = BooleanField(default=False)
    amo_contact_id = CharField(null=True)
    amo_deal_id = CharField(null=True)
    notes = CharField(null=True)

    class Meta:
        table_name = "mock_exam_applications"

    def __str__(self):
        return f"MockExamApplication {self.id} from User {self.user.user_id}"


_ALL_MODELS = (
    User,
    TrialApplication,
    PaymentApplication,
    SpeakingClubApplication,
    MockExamApplication,
)


def init_db() -> None:
    """Инициализация базы данных — создание таблиц при первом запуске."""
    try:
        db.connect(reuse_if_open=True)
        db.create_tables(_ALL_MODELS, safe=True)
        logger.info("Таблицы PostgreSQL проверены/созданы")
    except Exception as exc:
        logger.error("Не удалось подключиться к PostgreSQL: %s", exc)
        raise SystemExit(
            "Ошибка инициализации БД. Проверьте DATABASE_URL или POSTGRES_* в .env"
        ) from exc


def close_db() -> None:
    """Закрыть пул соединений при остановке бота."""
    if not db.is_closed():
        db.close()
