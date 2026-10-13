#!/usr/bin/env python3
"""Generate customer infrastructure instruction PDF (Cyrillic, A4)."""

from pathlib import Path

from fpdf import FPDF

FONT_DIR = Path.home() / "Library" / "Fonts"
OUT = Path(__file__).resolve().parent / "Инструкция_заказчику_инфраструктура.pdf"


class Doc(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(18, 16, 18)
        self.add_font("DejaVu", "", str(FONT_DIR / "DejaVuSans.ttf"))
        self.add_font("DejaVu", "B", str(FONT_DIR / "DejaVuSans-Bold.ttf"))
        self.add_font("DejaVu", "I", str(FONT_DIR / "DejaVuSans-Oblique.ttf"))
        self.add_font("DejaVuMono", "", str(FONT_DIR / "DejaVuSansMono.ttf"))

    def footer(self):
        self.set_y(-12)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(110, 110, 110)
        self.cell(0, 8, f"{self.page_no()}", align="C")
        self.set_text_color(0, 0, 0)

    def h1(self, text: str):
        self.ln(2)
        self.set_font("DejaVu", "B", 14)
        self.multi_cell(0, 7, text)
        self.ln(1)

    def h3(self, text: str):
        self.ln(1.5)
        self.set_font("DejaVu", "B", 10)
        self.multi_cell(0, 5.5, text)
        self.ln(0.5)

    def p(self, text: str):
        self.set_font("DejaVu", "", 9.5)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def bullet(self, text: str):
        self.set_x(self.l_margin)
        self.set_font("DejaVu", "", 9.5)
        self.cell(5, 5, "•")
        self.multi_cell(self.epw - 5, 5, text)
        self.ln(0.3)

    def numbered(self, n: int, text: str):
        self.set_x(self.l_margin)
        self.set_font("DejaVu", "", 9.5)
        self.cell(7, 5, f"{n}.")
        self.multi_cell(self.epw - 7, 5, text)
        self.ln(0.3)

    def note(self, text: str):
        self.set_font("DejaVu", "B", 9.5)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def mono_block(self, lines: list[str]):
        self.set_x(self.l_margin)
        self.set_fill_color(245, 245, 245)
        self.set_font("DejaVuMono", "", 8)
        usable = self.epw
        for line in lines:
            self.set_x(self.l_margin)
            self.multi_cell(usable, 4.2, line if line else " ", fill=True)
        self.ln(2)

    def table(self, headers: list[str], rows: list[list[str]], col_w: list[float]):
        line_h = 4.5

        def measure(cells: list[str]) -> float:
            self.set_font("DejaVu", "", 8.5)
            tallest = line_h + 1
            for cell, w in zip(cells, col_w):
                lines = self.multi_cell(
                    w - 2, line_h, cell or " ", dry_run=True, output="LINES"
                )
                tallest = max(tallest, line_h * max(1, len(lines)) + 1)
            return tallest

        def draw_row(cells: list[str], bold: bool = False):
            self.set_font("DejaVu", "B" if bold else "", 8.5)
            h = measure(cells)
            if self.get_y() + h > self.page_break_trigger:
                self.add_page()
            x0 = self.l_margin
            y0 = self.get_y()
            prev_auto = self.auto_page_break
            self.set_auto_page_break(False)
            if bold:
                self.set_fill_color(230, 230, 230)
            else:
                self.set_fill_color(255, 255, 255)
            for i, (cell, w) in enumerate(zip(cells, col_w)):
                x = x0 + sum(col_w[:i])
                self.rect(x, y0, w, h, style="DF")
                self.set_xy(x + 1, y0 + 0.5)
                self.multi_cell(w - 2, line_h, cell or " ")
            self.set_auto_page_break(prev_auto, margin=18)
            self.set_xy(x0, y0 + h)

        draw_row(headers, bold=True)
        for row in rows:
            draw_row(row, bold=False)
        self.set_x(self.l_margin)
        self.ln(2)


def build():
    pdf = Doc()
    pdf.add_page()

    pdf.set_font("DejaVu", "B", 16)
    pdf.multi_cell(0, 8, "Инструкция: подготовка инфраструктуры и доступов")
    pdf.ln(1)
    pdf.set_font("DejaVu", "", 9.5)
    pdf.multi_cell(
        0,
        5,
        "Документ описывает порядок заказа VPS, домена, DNS и прокси. "
        "Результат — готовый набор данных и доступов для дальнейшей настройки сервера.",
    )
    pdf.ln(2)

    # 1
    pdf.h1("1. Назначение документа")
    pdf.p(
        "Документ фиксирует шаги по подготовке инфраструктуры и перечень "
        "итоговых реквизитов. В объём входят: заказ VPS (Timeweb), покупка "
        "домена (reg.ru), DNS для двух поддоменов, покупка прокси (px6.me). "
        "Настройка приложений на сервере в этот документ не входит."
    )

    # 2
    pdf.h1("2. Итоговый чеклист: что должно быть готово")
    pdf.p("Готовые реквизиты и данные:")
    for b in [
        "VPS Timeweb (РФ): публичный IP, логин root, пароль root (из панели Timeweb)",
        "Домен, купленный на reg.ru",
        "Две DNS A-записи на IP сервера: pay.<домен> и vk.<домен>",
        "Прокси (рекомендуется px6.me): страна не РФ; поля: тип (HTTP или SOCKS5), host, port, login, password",
    ]:
        pdf.bullet(b)

    # A
    pdf.h1("3. Раздел A. VPS Timeweb (Россия)")
    pdf.h3("Цель")
    pdf.p(
        "Получить выделенный сервер в РФ и зафиксировать доступы для входа по SSH."
    )
    pdf.h3("Рекомендуемые параметры")
    pdf.table(
        ["Параметр", "Значение"],
        [
            ["Провайдер", "Timeweb Cloud (регион / дата-центр в РФ)"],
            ["vCPU", "2"],
            ["RAM", "2–4 ГБ (старт: 2 ГБ; запас: 4 ГБ)"],
            ["Диск", "SSD 20–40 ГБ"],
            ["ОС", "Ubuntu 22.04 LTS или Ubuntu 24.04 LTS"],
        ],
        [40, 132],
    )
    pdf.h3("Порядок действий")
    for i, t in enumerate(
        [
            "Зарегистрировать или войти в аккаунт Timeweb Cloud.",
            "Создать облачный сервер (VPS): раздел вроде «Облачные серверы» / «Создать сервер».",
            "Выбрать регион в Российской Федерации.",
            "Указать параметры из таблицы выше и ОС Ubuntu.",
            "При создании сервера выбрать вход по паролю root (пароль задаётся или выдаётся панелью Timeweb).",
            "Дождаться выдачи сервера.",
            "В панели Timeweb зафиксировать: публичный IPv4-адрес; логин root; пароль root (из карточки сервера / раздела доступов Timeweb).",
        ],
        1,
    ):
        pdf.numbered(i, t)
    pdf.h3("Итоговые данные (раздел A)")
    for b in [
        "Публичный IP сервера",
        "Логин: root",
        "Пароль root",
        "ОС и тариф (по желанию)",
    ]:
        pdf.bullet(b)
    pdf.h3("Ожидаемый результат")
    pdf.p("SSH-доступ к серверу в РФ под root с паролем из Timeweb.")

    # B
    pdf.h1("4. Раздел B. Домен на reg.ru")
    pdf.h3("Цель")
    pdf.p(
        "Иметь один домен второго уровня, на котором будут созданы два поддомена "
        "для HTTPS-эндпоинтов (платежи Т‑Банка и Callback VK). HTTPS обязателен "
        "для уведомлений банка."
    )
    pdf.h3("Порядок действий")
    for i, t in enumerate(
        [
            "Открыть reg.ru и проверить свободность желаемого имени (например, школа-домен.ru — здесь и далее условное имя).",
            "Купить свободный домен в зоне .ru / .рф / иной подходящей.",
            "Убедиться, что управление DNS доступно в личном кабинете reg.ru (стандартные NS reg.ru или свои — для A-записей достаточно панели DNS reg.ru).",
            "Дождаться активации домена (обычно от нескольких минут до нескольких часов).",
        ],
        1,
    ):
        pdf.numbered(i, t)
    pdf.h3("Итоговые данные (раздел B)")
    pdf.bullet("Полное имя домена (например, школа-домен.ru)")
    pdf.bullet("Подтверждение, что DNS управляется в ЛК reg.ru (или доступ к DNS)")
    pdf.h3("Ожидаемый результат")
    pdf.p("Активный домен с возможностью создавать A-записи для поддоменов.")

    # C
    pdf.h1("5. Раздел C. Два поддомена на одном домене")
    pdf.h3("Важно")
    pdf.p(
        "Нужен один домен и два поддомена, а не два отдельных домена. Оба "
        "поддомена указывают на один и тот же IP VPS."
    )
    pdf.table(
        ["Поддомен", "Назначение"],
        [
            [
                "pay.<домен>",
                "HTTPS для webhook платежей Telegram-бота и уведомлений Т‑Банка (Notification / Success / Fail)",
            ],
            [
                "vk.<домен>",
                "HTTPS для Callback API сообщества ВКонтакте",
            ],
        ],
        [40, 132],
    )
    pdf.p("Пример условного домена: школа-домен.ru.")
    pdf.bullet("pay.школа-домен.ru — платежи и банк")
    pdf.bullet("vk.школа-домен.ru — ВКонтакте")

    pdf.h3("Порядок создания A-записей в DNS reg.ru")
    for i, t in enumerate(
        [
            "Войти в личный кабинет reg.ru → домен → управление зоной DNS (или «DNS-серверы и зона»).",
            "Добавить запись типа A: имя/хост pay; значение — публичный IPv4 сервера Timeweb; TTL 300–3600 с (или по умолчанию).",
            "Добавить вторую запись типа A: имя/хост vk; значение — тот же IPv4 сервера; TTL аналогично.",
            "Сохранить изменения.",
            "Дождаться распространения DNS (обычно от нескольких минут до 24 часов; чаще — до 1–2 часов).",
        ],
        1,
    ):
        pdf.numbered(i, t)
    pdf.p(
        "Не создавать отдельные домены pay.ru и vk.ru. Не путать A-запись "
        "поддомена с записью на корень (@ / сам домен) — критичны именно pay и vk."
    )

    pdf.h3("Итоговые данные (раздел C)")
    for b in [
        "Домен",
        "Подтверждение A-записей pay и vk → IP",
    ]:
        pdf.bullet(b)
    pdf.h3("Ожидаемый результат")
    pdf.p("Оба FQDN резолвятся в IP VPS.")

    # D
    pdf.h1("6. Раздел D. Прокси для Telegram Bot API")
    pdf.h3("Цель")
    pdf.p(
        "Сервер в РФ часто не имеет стабильного прямого доступа к "
        "api.telegram.org. Прокси нужен только для исходящих запросов "
        "Telegram-бота к Telegram API."
    )
    pdf.p("Прокси не используется для:")
    for b in [
        "запросов к API Т‑Банка;",
        "работы VK-бота;",
        "приёма входящих webhook/notification от банка (они приходят на pay.<домен> напрямую).",
    ]:
        pdf.bullet(b)

    pdf.h3("Рекомендуемый сервис")
    pdf.p("Сервис: https://px6.me/ru/user/proxy (личный кабинет прокси px6).")

    pdf.h3("Обязательное требование по стране")
    pdf.note(
        "Страна выхода прокси не должна быть Россией (РФ). Выбрать любую другую "
        "страну, с которой api.telegram.org доступен с российского VPS через "
        "этот прокси. Прокси с локацией «Россия» / РФ не подходит."
    )

    pdf.h3("Какие поля зафиксировать в ЛК px6")
    pdf.table(
        ["Поле", "Описание"],
        [
            ["Тип", "HTTP или SOCKS5 (как выдан в ЛК)"],
            ["Host", "адрес (IP или hostname) прокси"],
            ["Port", "порт"],
            ["Login", "логин"],
            ["Password", "пароль"],
            ["Страна", "не РФ (указать выбранную страну)"],
        ],
        [35, 137],
    )
    pdf.p("Пример записи реквизитов:")
    pdf.mono_block(
        [
            "socks5://login:password@host:port",
            "http://login:password@host:port",
        ]
    )

    pdf.h3("Порядок действий")
    for i, t in enumerate(
        [
            "Зарегистрироваться / войти на https://px6.me/ru/user/proxy.",
            "Купить или выделить прокси с выходом не в РФ.",
            "В карточке прокси зафиксировать: host, port, login, password, тип (HTTP или SOCKS5), страна.",
        ],
        1,
    ):
        pdf.numbered(i, t)
    pdf.h3("Ожидаемый результат")
    pdf.p(
        "Готовые реквизиты прокси (тип, host, port, login, password, страна ≠ РФ) "
        "для исходящих запросов только к Telegram API. VK и Т‑Банк работают без "
        "этого прокси."
    )

    pdf.output(str(OUT))
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
