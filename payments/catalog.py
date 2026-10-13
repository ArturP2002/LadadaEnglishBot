"""Каталог оплачиваемых продуктов (суммы в рублях — без изменений)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PaymentProduct:
    course: str
    period: str  # "2_weeks" | "1_month"
    amount_rub: int
    notes: str
    description: str


_PRODUCTS: dict[str, PaymentProduct] = {
    "pay_2_weeks": PaymentProduct(
        course="ege",
        period="2_weeks",
        amount_rub=6000,
        notes="ЕГЭ basic",
        description="ЕГЭ basic — 2 недели",
    ),
    "pay_2_weeks_basic": PaymentProduct(
        course="ege",
        period="2_weeks",
        amount_rub=6000,
        notes="ЕГЭ basic",
        description="ЕГЭ basic — 2 недели",
    ),
    "pay_2_weeks_slay": PaymentProduct(
        course="ege",
        period="2_weeks",
        amount_rub=6000,
        notes="ЕГЭ slay",
        description="ЕГЭ slay — 2 недели",
    ),
    "pay_1_month": PaymentProduct(
        course="ege",
        period="1_month",
        amount_rub=12000,
        notes="ЕГЭ basic",
        description="ЕГЭ basic — 1 месяц",
    ),
    "pay_1_month_basic": PaymentProduct(
        course="ege",
        period="1_month",
        amount_rub=12000,
        notes="ЕГЭ basic",
        description="ЕГЭ basic — 1 месяц",
    ),
    "pay_1_month_slay": PaymentProduct(
        course="ege",
        period="1_month",
        amount_rub=12000,
        notes="ЕГЭ slay",
        description="ЕГЭ slay — 1 месяц",
    ),
    "pay_dvi_2_weeks": PaymentProduct(
        course="dvi",
        period="2_weeks",
        amount_rub=10000,
        notes="ДВИ МГИМО",
        description="ДВИ МГИМО — 2 недели",
    ),
    "pay_dvi_1_month": PaymentProduct(
        course="dvi",
        period="1_month",
        amount_rub=20000,
        notes="ДВИ МГИМО",
        description="ДВИ МГИМО — 1 месяц",
    ),
    "pay_olympics_2_weeks": PaymentProduct(
        course="olympics",
        period="2_weeks",
        amount_rub=6000,
        notes="Олимпиады",
        description="Олимпиады — 2 недели",
    ),
    "pay_olympics_1_month": PaymentProduct(
        course="olympics",
        period="1_month",
        amount_rub=12000,
        notes="Олимпиады",
        description="Олимпиады — 1 месяц",
    ),
}


def get_product(callback_data: str) -> Optional[PaymentProduct]:
    return _PRODUCTS.get(callback_data)
