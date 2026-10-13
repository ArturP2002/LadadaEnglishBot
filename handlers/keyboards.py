from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопками для стартового сообщения"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💅🏼 Записаться на бесплатное занятие",
                callback_data="trial_lesson"
            )
        ],
        [
            InlineKeyboardButton(
                text="Узнать о школе, занятиях и активностях",
                callback_data="about_school"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎀 Купить курс «Плати за 2, получай 7»",
                callback_data="buy_course_main",
            )
        ],
        [
            InlineKeyboardButton(
                text="Посмотреть отзывы",
                callback_data="reviews"
            )
        ],
        [
            InlineKeyboardButton(
                text="Скачать бесплатные материалы",
                callback_data="free_materials"
            )
        ]
    ])
    return keyboard


def get_trial_lesson_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для страницы пробного занятия"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💅🏼 Записаться на бесплатное пробное",
                callback_data="signup_trial"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎀 Купить курс «Плати за 2, получай 7»",
                callback_data="buy_course"
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                callback_data="home"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home"
            )
        ]
    ])
    return keyboard


def get_signup_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для страницы подтверждения заявки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home"
            )
        ]
    ])
    return keyboard


def get_price_track_keyboard(
    *,
    show_back: bool = True,
    main_flow: bool = False,
    buy_flow: bool = False,
    back_callback: str = "about_school",
) -> InlineKeyboardMarkup:
    """Выбор направления: ЕГЭ/ОГЭ, ДВИ или олимпиады.

    main_flow — переход с главного экрана («Купить курс»): без «Назад», отдельные callback,
    чтобы возврат с прайса снова открывал эту же клавиатуру.

    buy_flow — «Купить курс» из остальных разделов: те же направления, «Назад» обычно на home.

    back_callback — куда ведёт «Назад» (по умолчанию сценарий после «Узнать прайс» из «О школе»).
    """
    if buy_flow:
        ege_cb = "price_ege_from_buy"
        dvi_cb = "price_dvi_from_buy"
        olympics_cb = "price_olympics_from_buy"
    elif main_flow:
        ege_cb = "price_ege_from_main"
        dvi_cb = "price_dvi_from_main"
        olympics_cb = "price_olympics_from_main"
    else:
        ege_cb = "price_ege_oge"
        dvi_cb = "price_dvi"
        olympics_cb = "price_olympics"
    rows = [
        [
            InlineKeyboardButton(
                text="Подготовиться к ЕГЭ или ОГЭ",
                callback_data=ege_cb,
            )
        ],
        [
            InlineKeyboardButton(
                text="Подготовиться к ДВИ МГИМО",
                callback_data=dvi_cb,
            )
        ],
        [
            InlineKeyboardButton(
                text="Подготовиться к олимпиадам",
                callback_data=olympics_cb,
            )
        ],
    ]
    if show_back:
        rows.append(
            [
                InlineKeyboardButton(
                    text="Назад",
                    callback_data=back_callback,
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_dvi_course_info_keyboard(*, track_back_callback: str = "price_track") -> InlineKeyboardMarkup:
    """Клавиатура прайса ДВИ (те же подписи, отдельные callback для заявок)."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Оплатить занятия на 2 недели",
                callback_data="pay_dvi_2_weeks",
            )
        ],
        [
            InlineKeyboardButton(
                text="Оплатить занятия на 1 месяц",
                callback_data="pay_dvi_1_month",
            )
        ],
        [
            InlineKeyboardButton(
                text="💅🏼 Записаться на бесплатное пробное",
                callback_data="signup_trial_dvi",
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                callback_data=track_back_callback,
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home",
            )
        ],
    ])
    return keyboard


def get_olympics_course_info_keyboard(*, track_back_callback: str = "price_track") -> InlineKeyboardMarkup:
    """Клавиатура прайса олимпиад (отдельные callback для заявок)."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Оплатить занятия на 2 недели",
                callback_data="pay_olympics_2_weeks",
            )
        ],
        [
            InlineKeyboardButton(
                text="Оплатить занятия на 1 месяц",
                callback_data="pay_olympics_1_month",
            )
        ],
        [
            InlineKeyboardButton(
                text="💅🏼 Записаться на бесплатное пробное",
                callback_data="signup_trial_olympics",
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                callback_data=track_back_callback,
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home",
            )
        ],
    ])
    return keyboard


_EGE_BACK_CODES = {
    "price_track_main": "m",
    "price_track": "t",
    "home": "h",
    "signup_additional_activities": "a",
    "buy_course": "b",
}


def _ege_back_code(course_back_callback: str) -> str:
    return _EGE_BACK_CODES.get(course_back_callback, "t")


def get_ege_tariff_keyboard(course_back_callback: str = "price_track") -> InlineKeyboardMarkup:
    """Выбор тарифа ЕГЭ/ОГЭ перед оплатой."""
    code = _ege_back_code(course_back_callback)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Выбрать slay тариф",
                callback_data=f"ege_tariff_slay_{code}",
            )
        ],
        [
            InlineKeyboardButton(
                text="Выбрать basic тариф",
                callback_data=f"ege_tariff_basic_{code}",
            )
        ],
        [
            InlineKeyboardButton(
                text="💅🏼 Записаться на бесплатное пробное",
                callback_data="signup_trial",
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                callback_data=course_back_callback,
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home",
            )
        ],
    ])
    return keyboard


def get_course_info_keyboard(
    course_back_callback: str = "price_track",
    *,
    tariff: str = "basic",
) -> InlineKeyboardMarkup:
    """Клавиатура оплаты ЕГЭ/ОГЭ после выбора тарифа."""
    code = _ege_back_code(course_back_callback)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Оплатить занятия на 2 недели",
                callback_data=f"pay_2_weeks_{tariff}",
            )
        ],
        [
            InlineKeyboardButton(
                text="Оплатить занятия на 1 месяц",
                callback_data=f"pay_1_month_{tariff}",
            )
        ],
        [
            InlineKeyboardButton(
                text="💅🏼 Записаться на бесплатное пробное",
                callback_data="signup_trial",
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                callback_data=f"ege_tariff_menu_{code}",
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home",
            )
        ],
    ])
    return keyboard


def get_payment_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для страницы подтверждения оплаты"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home"
            )
        ]
    ])
    return keyboard


def get_payment_link_keyboard(payment_url: str) -> InlineKeyboardMarkup:
    """Клавиатура со ссылкой на оплату Т‑Банка."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💳 Перейти к оплате",
                url=payment_url,
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home",
            )
        ],
    ])


def get_about_school_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для страницы 'О школе'"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💅🏼 Записаться на бесплатное пробное",
                callback_data="signup_trial"
            )
        ],
        [
            InlineKeyboardButton(
                text="Выбрать преподавателя",
                callback_data="choose_teacher"
            )
        ],
        [
            InlineKeyboardButton(
                text="Посмотреть расписание и формат",
                callback_data="schedule_format"
            )
        ],
        [
            InlineKeyboardButton(
                text="Узнать прайс",
                callback_data="price_info"
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                callback_data="home"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home"
            )
        ]
    ])
    return keyboard


def get_teachers_list_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру со списком преподавателей"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎀 Лада",
                callback_data="teacher_1"
            ),
            InlineKeyboardButton(
                text="🎓 Майкл",
                callback_data="teacher_2"
            )
        ],
        [
            InlineKeyboardButton(
                text="🐈 Дарья",
                callback_data="teacher_3"
            ),
            InlineKeyboardButton(
                text="🛹 Даша",
                callback_data="teacher_4"
            )
        ],
        [
            InlineKeyboardButton(
                text="📚 Влада",
                callback_data="teacher_5"
            ),
            InlineKeyboardButton(
                text="🌍 Соня",
                callback_data="teacher_6"
            )
        ],
        [
            InlineKeyboardButton(
                text="☕️ Аня",
                callback_data="teacher_7"
            ),
            InlineKeyboardButton(
                text="👓 Мария",
                callback_data="teacher_8"
            )
        ],
        [
            InlineKeyboardButton(
                text="🍪 Юлия",
                callback_data="teacher_9"
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                callback_data="about_school"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home"
            )
        ]
    ])
    return keyboard


def get_teacher_keyboard(teacher_id: int, total_teachers: int = 9) -> InlineKeyboardMarkup:
    """Создает клавиатуру для страницы конкретного преподавателя с навигацией"""
    keyboard_buttons = []
    
    # Кнопки действий
    keyboard_buttons.append([
        InlineKeyboardButton(
            text="💅🏼 Записаться на бесплатное пробное",
            callback_data=f"signup_trial_teacher_{teacher_id}"
        )
    ])
    keyboard_buttons.append([
        InlineKeyboardButton(
            text="🎀 Купить курс «Плати за 2, получай 7»",
            callback_data="buy_course"
        )
    ])
    
    # Навигация между преподавателями
    nav_buttons = []
    if teacher_id > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="<<< Previous eng mom",
                callback_data=f"teacher_{teacher_id - 1}"
            )
        )
    if teacher_id < total_teachers:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Next eng mom >>>",
                callback_data=f"teacher_{teacher_id + 1}"
            )
        )
    
    if nav_buttons:
        keyboard_buttons.append(nav_buttons)

    keyboard_buttons.append([
        InlineKeyboardButton(
            text="Назад ко всем eng moms",
            callback_data="choose_teacher"
        )
    ])
    keyboard_buttons.append([
        InlineKeyboardButton(
            text="🏠 Домой",
            callback_data="home"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def get_schedule_format_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для страницы расписания и формата обучения"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💅🏼 Записаться на бесплатное пробное",
                callback_data="signup_trial"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎀 Купить курс «Плати за 2, получай 7»",
                callback_data="buy_course"
            )
        ],
        [
            InlineKeyboardButton(
                text="Посмотреть учебную платформу",
                callback_data="study_platform"
            )
        ],
        [
            InlineKeyboardButton(
                text="Записаться на доп активности",
                callback_data="signup_additional_activities"
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                callback_data="about_school"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home"
            )
        ]
    ])
    return keyboard


def get_study_platform_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура экрана учебной платформы (без кнопки перехода на платформу)."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💅🏼 Записаться на бесплатное пробное",
                callback_data="signup_trial"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎀 Купить курс «Плати за 2, получай 7»",
                callback_data="buy_course"
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                callback_data="schedule_format"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home"
            )
        ]
    ])
    return keyboard


def get_additional_activities_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для страницы дополнительных активностей"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💅🏼 Записаться на бесплатное пробное",
                callback_data="signup_trial"
            )
        ],
        [
            InlineKeyboardButton(
                text="Узнать о спикинг клабе",
                callback_data="speaking_club_info"
            )
        ],
        [
            InlineKeyboardButton(
                text="Узнать о пробниках с экспертами",
                callback_data="mock_exams_info"
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                callback_data="schedule_format"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home"
            )
        ]
    ])
    return keyboard


def get_speaking_club_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для страницы информации о спикинг клабе"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Записаться на спикинг клаб",
                callback_data="signup_speaking_club"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎀 Купить курс «Плати за 2, получай 7»",
                callback_data="buy_course"
            )
        ],
        [
            InlineKeyboardButton(
                text="💅🏼 Записаться на бесплатное пробное",
                callback_data="signup_trial"
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                callback_data="signup_additional_activities"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home"
            )
        ]
    ])
    return keyboard


def get_mock_exams_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для страницы информации о пробниках с экспертами"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Записаться на пробник с экспертами",
                callback_data="signup_mock_exam"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎀 Купить курс «Плати за 2, получай 7»",
                callback_data="buy_course"
            )
        ],
        [
            InlineKeyboardButton(
                text="💅🏼 Записаться на бесплатное пробное",
                callback_data="signup_trial"
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                callback_data="signup_additional_activities"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home"
            )
        ]
    ])
    return keyboard


def get_reviews_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для страницы отзывов"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💅🏼 Записаться на бесплатное пробное",
                callback_data="signup_trial"
            )
        ],
        [
            InlineKeyboardButton(
                text="Читать отзывы",
                callback_data="read_reviews"
            )
        ],
        [
            InlineKeyboardButton(
                text="Посмотреть больше отзывов",
                callback_data="otzovik_reviews",
                url="https://otzovik.com/reviews/ladada_english-onlayn_repetitor_po_angliyskomu_yaziku/"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎀 Купить курс «Плати за 2, получай 7»",
                callback_data="buy_course"
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                callback_data="home"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home"
            )
        ]
    ])
    return keyboard


def get_review_keyboard(
    review_id: int,
    next_author_genitive: str,
    total_reviews: int = 6,
) -> InlineKeyboardMarkup:
    """Клавиатура отзыва; next_author_genitive — имя в род. п. для «Читать отзыв от …»."""
    # Вычисляем номер следующего отзыва (по кругу)
    next_review_id = (review_id % total_reviews) + 1
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💅🏼 Записаться на бесплатное пробное",
                callback_data="signup_trial"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Читать отзыв от {next_author_genitive}",
                callback_data=f"review_{next_review_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="Посмотреть больше отзывов",
                callback_data="otzovik_reviews",
                url="https://otzovik.com/reviews/ladada_english-onlayn_repetitor_po_angliyskomu_yaziku/"
            )
        ],
        [
            InlineKeyboardButton(
                text="🎀 Купить курс «Плати за 2, получай 7»",
                callback_data="buy_course"
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                callback_data="reviews"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home"
            )
        ]
    ])
    return keyboard


def get_free_materials_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для страницы бесплатных материалов"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💅🏼 Записаться на бесплатное пробное",
                callback_data="signup_trial"
            )
        ],
        [
            InlineKeyboardButton(
                text="📥 Скачать материалы для ЕГЭ",
                callback_data="materials_ege"
            )
        ],
        [
            InlineKeyboardButton(
                text="📥 Скачать материалы для олимпиад",
                callback_data="materials_olympiad"
            )
        ],
        [
            InlineKeyboardButton(
                text="🤖 Запустить AI-бота и набрать сотку",
                url="https://t.me/Ladada_eng_trainer_bot"
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                callback_data="home"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home"
            )
        ]
    ])
    return keyboard


def get_ege_materials_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру раздела материалов ЕГЭ"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📥 Все 30-36, которые встречаются в ЕГЭ",
                callback_data="download_material_ege_30_36"
            )
        ],
        [
            InlineKeyboardButton(
                text="📥 Вся Россия в одной PDF",
                callback_data="download_material_ege_all_russia"
            )
        ],
        [
            InlineKeyboardButton(
                text="📥 Первое задание спикинга",
                callback_data="download_material_ege_adv_disadv"
            )
        ],
        [
            InlineKeyboardButton(
                text="📥 Второе задание ЕГЭ",
                callback_data="download_material_ege_task_2"
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                callback_data="free_materials"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home"
            )
        ]
    ])
    return keyboard


def get_olympiad_materials_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру раздела материалов олимпиад"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📥 Отцы-основатели и США",
                callback_data="download_material_olympiad_founding_fathers"
            )
        ],
        [
            InlineKeyboardButton(
                text="📥 Литература для олимпиад",
                callback_data="download_material_olympiad_literature"
            )
        ],
        [
            InlineKeyboardButton(
                text="Назад",
                callback_data="free_materials"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home"
            )
        ]
    ])
    return keyboard


def get_after_download_keyboard(back_callback_data: str = "free_materials") -> InlineKeyboardMarkup:
    """Создает клавиатуру после скачивания материала"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Хочу ещё пользу",
                callback_data=back_callback_data
            )
        ],
        [
            InlineKeyboardButton(
                text="💅🏼 Записаться на бесплатное пробное",
                callback_data="signup_trial"
            )
        ],
        [
            InlineKeyboardButton(
                text="🤖 Запустить AI-бота и набрать сотку",
                url="https://t.me/Ladada_eng_trainer_bot"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Домой",
                callback_data="home"
            )
        ]
    ])
    return keyboard
