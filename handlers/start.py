
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import MessageEntityType
import os
import config
from database.models import User, TrialApplication, PaymentApplication, SpeakingClubApplication, MockExamApplication
from datetime import datetime
from aiogram.utils.formatting import BlockQuote, CustomEmoji, Text, Bold
import asyncio
import logging
import json
import base64
import urllib.request
import urllib.error
import amo_crm_secrets
from integrations.google_sheets import append_sheet_row_async, build_row_for_application
from utils import media_cache
from handlers.keyboards import (
    get_start_keyboard,
    get_trial_lesson_keyboard,
    get_signup_confirmation_keyboard,
    get_price_track_keyboard,
    get_course_info_keyboard,
    get_ege_tariff_keyboard,
    _EGE_BACK_CODES,
    get_dvi_course_info_keyboard,
    get_olympics_course_info_keyboard,
    get_payment_confirmation_keyboard,
    get_payment_link_keyboard,
    get_about_school_keyboard,
    get_teachers_list_keyboard,
    get_teacher_keyboard,
    get_schedule_format_keyboard,
    get_study_platform_keyboard,
    get_additional_activities_keyboard,
    get_speaking_club_keyboard,
    get_mock_exams_keyboard,
    get_reviews_keyboard,
    get_review_keyboard,
    get_free_materials_keyboard,
    get_ege_materials_keyboard,
    get_olympiad_materials_keyboard,
    get_after_download_keyboard
)
# from payments.service import create_payment_for_callback, get_payment_link_message
# from payments.tbank import TBankError

logger = logging.getLogger(__name__)

router = Router()

# Данные о преподавателях
TEACHERS = [
    {
        "id": 1,
        "name": "Лада",
        "name_instrumental": "Ладой",
        "video_path": "all_media/TeacherVideos/Lada.mp4"
    },
    {
        "id": 2,
        "name": "Майкл",
        "name_instrumental": "Майклом",
        "video_path": "all_media/TeacherVideos/Michael.mp4"
    },
    {
        "id": 3,
        "name": "Дарья",
        "name_instrumental": "Дарьей",
        "video_path": "all_media/TeacherVideos/Darya.mp4"
    },
    {
        "id": 4,
        "name": "Даша",
        "name_instrumental": "Дашей",
        "video_path": "all_media/TeacherVideos/Dasha.mp4"
    },
    {
        "id": 5,
        "name": "Влада",
        "name_instrumental": "Владой",
        "video_path": "all_media/TeacherVideos/Vlada.mp4"
    },
    {
        "id": 6,
        "name": "Соня",
        "name_instrumental": "Соней",
        "video_path": "all_media/TeacherVideos/Sonya.mp4"
    },
    {
        "id": 7,
        "name": "Аня",
        "name_instrumental": "Аней",
        "video_path": "all_media/TeacherVideos/Ana.mp4"
    },
    {
        "id": 8,
        "name": "Мария",
        "name_instrumental": "Марией",
        "video_path": "all_media/TeacherVideos/Maria.mp4"
    },
    {
        "id": 9,
        "name": "Юлия",
        "name_instrumental": "Юлией",
        "video_path": "all_media/TeacherVideos/Yulia.mp4"
    }
]

# Размеры видео при отправке (Telegram sendVideo: width × height)
VIDEO_SEND_WIDTH = 1080
VIDEO_SEND_HEIGHT = 1350
WELCOME_VIDEO_PATH = "all_media/WelcomeVideo.mp4"

# Выбор направления: ЕГЭ/ОГЭ, ДВИ или олимпиады (см. get_price_track_keyboard). Премиум 🎀 — набор ladadaeng.
PRICE_TRACK_PROMPT = Text(
    "К чему хочешь подготовиться? ",
    CustomEmoji("🎀", custom_emoji_id="5199582550653163382"),
)

DVI_PHOTO_1 = "all_media/DVI1.jpg"
DVI_PHOTO_2 = "all_media/DVI2.jpg"

NEW_PRICE_PHOTOS = [
    f"all_media/NewPriceMedia/NewPrice{i}.jpg" for i in range(1, 5)
]

OLYMPICS_PHOTOS = [
    "all_media/OlympicsPhotos/Olympics1.jpg",
    "all_media/OlympicsPhotos/Olympics2.jpg",
]

STUDY_PLATFORM_PHOTOS = [
    "all_media/StudyPlatform/Platform1.jpg",
    "all_media/StudyPlatform/Platform2.jpg",
]

# Видео блока «Спикинг клуб» (sendVideo; имя файла как на диске — важно для Linux)
SPEAKING_CLUB_VIDEO_PATH = "all_media/SpeakingMedia/SpeakingVideo.mp4"
SPEAKING_CLUB_VIDEO_WIDTH = 1024
SPEAKING_CLUB_VIDEO_HEIGHT = 1280

# Данные о бесплатных материалах
MATERIALS = {
    "ege_30_36": {
        "title": "Все 30-36, которые встречаются в ЕГЭ",
        "description": "Подборка всех заданий 30-36 для отработки.",
        "file_path": "materials/EGE/30-36.pdf",
        "section_callback": "materials_ege",
    },
    "ege_all_russia": {
        "title": "Вся Россия в одной PDF",
        "description": "Материал по теме «Вся Россия» в одном файле.",
        "file_path": "materials/EGE/AllRussia.pdf",
        "section_callback": "materials_ege",
    },
    "ege_adv_disadv": {
        "title": "Все плюсы и минусы на спикинге (задание 1)",
        "description": "Плюсы и минусы для Speaking, задание 1.",
        "file_path": "materials/EGE/AdvAndDisadv.pdf",
        "section_callback": "materials_ege",
    },
    "ege_task_2": {
        "title": "Второе задание ЕГЭ",
        "description": "Материалы для второго задания ЕГЭ.",
        "file_path": "materials/EGE/Task2.pdf",
        "section_callback": "materials_ege",
    },
    "olympiad_founding_fathers": {
        "title": "Отцы-основатели и США",
        "description": "Материал для олимпиадной темы про founding fathers.",
        "file_path": "materials/Olimpiad/TheFoundingFathers.pdf",
        "section_callback": "materials_olympiad",
    },
    "olympiad_literature": {
        "title": "Американская и британская литература",
        "description": "Материал для олимпиадной темы по литературе.",
        "file_path": "materials/Olimpiad/AmericanAndBritishLiterature.pdf",
        "section_callback": "materials_olympiad",
    },
}

# Отзывы: карточка = фото; author_genitive — имя в род. п. для кнопки «Читать отзыв от …»
REVIEWS = [
    {"id": 1, "author": "Катя", "author_genitive": "Кати", "author_genitive_with_university": "Кати из ВШЭ", "photo_path": "all_media/ReviewsPhoto/KatyaReview.PNG"},
    {"id": 2, "author": "Мария", "author_genitive": "Марии", "author_genitive_with_university": "Марии из МГИМО", "photo_path": "all_media/ReviewsPhoto/MariaReview.PNG"},
    {"id": 3, "author": "Таня", "author_genitive": "Тани", "author_genitive_with_university": "Тани из ВШЭ", "photo_path": "all_media/ReviewsPhoto/TanyaReview.PNG"},
    {"id": 4, "author": "Вика", "author_genitive": "Вики", "author_genitive_with_university": "Вики из МГУ", "photo_path": "all_media/ReviewsPhoto/VikaReview.PNG"},
    {"id": 5, "author": "Мария", "author_genitive": "Марии", "author_genitive_with_university": "Марии из ВШЭ", "photo_path": "all_media/ReviewsPhoto/Maria2.PNG"},
    {"id": 6, "author": "Влада", "author_genitive": "Влады", "author_genitive_with_university": "Влады из МГУ", "photo_path": "all_media/ReviewsPhoto/VladaReview.PNG"},
]

def get_start_message() -> Text:
    """Формирует текст стартового сообщения с премиум-эмодзи"""
    text = Text(
        "Heeey, bestie ",
        CustomEmoji("🎀", custom_emoji_id="5199582550653163382"),
        "\n\n",
        "Ты только что нашла место, где делают",
        CustomEmoji("8️⃣", custom_emoji_id="5233731599400468187"),
        CustomEmoji("5️⃣", custom_emoji_id="5233620226603515410"),
        Bold("+ за ЕГЭ по английскому без стресса и токсичных преподов,"),
        " готовят к олимпиадам, ДВИ И ОГЭ\n\n",
        CustomEmoji("👓", custom_emoji_id="5348418028046409800"),
        " Здесь ты можешь:\n\n",
        CustomEmoji("1️⃣", custom_emoji_id="5233490806353984161"),
        " записаться на ",
        Bold("бесплатное пробное занятие"),
        ", получить стратегию поступления и наконец понять, какой у тебя уровень\n",
        CustomEmoji("2️⃣", custom_emoji_id="5231403405003488089"),
        " узнать о всех ",
        Bold("дополнительных активностях"),
        ", на которые можно попасть, даже не обучаясь в ladada_eng\n",
        CustomEmoji("3️⃣", custom_emoji_id="5231333942497411730"),
        " забрать ",
        Bold("бесплатные материалы"), "\n",
        CustomEmoji("4️⃣", custom_emoji_id="5231093836645695347"),
        " ",
        Bold("купить курс сразу"),
        " по системе «Плати за 2, получай 7»\n\n",
        Bold("Записывайся на пробное занятие или сразу забирай место в группе. "),
        Bold("See you at your glow-up era"),
        " ",
        CustomEmoji("⬇️", custom_emoji_id="5231486087418905312"),
        CustomEmoji("💪", custom_emoji_id="5231150766437195986"),
    )
    return text


def get_trial_lesson_message() -> Text:
    """Формирует текст сообщения о пробном занятии"""
    text = Text(
        "Bestik, мы понимаем, что у тебя сейчас в голове куча вопросов:\n",
        CustomEmoji("🔴", custom_emoji_id="5350663780546142388"),
        "Я успею подготовиться?\n",
        CustomEmoji("🔴", custom_emoji_id="5350663780546142388"),
        "А если у меня слабый уровень?\n",
        CustomEmoji("🔴", custom_emoji_id="5350663780546142388"),
        "Как проходят уроки?\n\n",
        "Take a breath, это нормально ", 
        CustomEmoji("🎀", custom_emoji_id="5199582550653163382"),
        "\n\n",
        "Именно для этого у нас есть ", Bold("бесплатное пробное занятие"), 
        CustomEmoji("📚", custom_emoji_id="5350407701711053269"),
        "- это полноценный онлайн-урок в Zoom длительностью ~30 минут\n\n",
        "На нём мы:\n",
        BlockQuote(
            CustomEmoji("🔴", custom_emoji_id="5350663780546142388"),
            "определим твой уровень английского без страшных тестов\n",
            CustomEmoji("🔴", custom_emoji_id="5350663780546142388"),
            "покажем, как проходят наши занятия вживую\n",
            CustomEmoji("🔴", custom_emoji_id="5350663780546142388"),
            "разберём, какие темы нужно подтянуть именно тебе\n",
            CustomEmoji("🔴", custom_emoji_id="5350663780546142388"),
            "соберём понятную стратегию подготовки и поступления\n",
            CustomEmoji("🔴", custom_emoji_id="5350663780546142388"),
            "ответим на ВСЕ твои вопросы\n",
        ),
        "\n\n",
        "Обещаем не настаивать на покупке курса и не названивать после урока. English moms на твоей стороне 🫂\n\n",
        Bold("Записывайся на пробное. See you soon, future 85+ girl "),
        CustomEmoji("🍪", custom_emoji_id="5231456735612400746"),
    )
    return text


def get_signup_confirmation_message() -> Text:
    """Формирует текст сообщения подтверждения заявки"""
    text = Text(
        Bold("Yaaay, bestik, заявка получена "),
        CustomEmoji("🎀", custom_emoji_id="5199582550653163382"),
        "\n\n",
        "Совсем скоро наш менеджер напишет тебе с аккаунта @ladadada_boss\n\n",
        Bold("Проверь, пожалуйста, что личные сообщения открыты"),
        "\n\n",
        "А пока можешь погулять по боту: скачать полезные материалы, посмотреть отзывы, "
        "изучить additional activities ",
        CustomEmoji("❤️", custom_emoji_id="5199677078588382034"),
        "\n\n",
        "Для этого нажми кнопку «Домой». Твоя заявка никуда не потеряется ",
        CustomEmoji("🍪", custom_emoji_id="5231456735612400746"),
    )
    return text


def get_course_info_message() -> Text:
    """Формирует текст сообщения с информацией о курсе"""
    text = Text(
        "Bestie, ", Bold("самое важное "),
        CustomEmoji("💌", custom_emoji_id="5418031330426395309"),
        "\n\n",
        "У нас есть два формата обучения:\n\n",
        CustomEmoji("🎀", custom_emoji_id="5199582550653163382"),
        Bold(" базовый "),
        CustomEmoji("➡️", custom_emoji_id="5231353755181545862"),
        " если нужна сильная подготовка к ЕГЭ в мини-группе\n\n",
        CustomEmoji("💅", custom_emoji_id="5431384126051624738"),
        Bold(" расширенный slay "),
        CustomEmoji("➡️", custom_emoji_id="5231353755181545862"),
        " если нужна сильная подготовка к ЕГЭ и сопровождение до поступления в топовый вуз: "
        "с проверкой работ от эксперта, помощью с олимпиадами, ДВИ и полным планом поступления\n\n",
        "Самый вайб: система ", Bold("«Плати за 2, получай 7»"), "\n\n",
        CustomEmoji("➡️", custom_emoji_id="5231353755181545862"),
        " Кроме основных занятий ты ", Bold("бесплатно получаешь дополнительные активности каждую неделю:"), "\n",
        BlockQuote(
            CustomEmoji("🩷", custom_emoji_id="5350487386239296216"),
            "клуб 30-36 и grammar club\n",
            CustomEmoji("🩷", custom_emoji_id="5350487386239296216"),
            "speaking club\n",
            CustomEmoji("🩷", custom_emoji_id="5350487386239296216"),
            "reading club\n",
            CustomEmoji("🩷", custom_emoji_id="5350487386239296216"),
            "проверка домашних работ\n",
            CustomEmoji("🩷", custom_emoji_id="5350487386239296216"),
            "все материалы и Cambridge учебники",
        ),
        "\n\n",
        "Если не можешь выбрать формат, ", Bold("приходи на бесплатное пробное занятие "),
        CustomEmoji("➡️", custom_emoji_id="5231353755181545862"),
        " определим твой уровень, найдём слабые места и составим план подготовки к вузу мечты ",
        CustomEmoji("❤️", custom_emoji_id="5199677078588382034"),
        CustomEmoji("💪", custom_emoji_id="5231150766437195986"),
    )
    return text


def get_dvi_course_info_message() -> Text:
    """Текст прайса и условий подготовки к ДВИ МГИМО (подпись к медиа-группе)"""
    text = Text(
        "Students, подготовку к ", Bold("ДВИ МГИМО"), " мы выделили в отдельный формат\n\n",
        "Стоимость занятий - ", Bold("2500 ₽/час"), " в маленьких группах по 6-7 students "
        "с одинаковыми уровнем знаний и целью ",
        CustomEmoji("🎀", custom_emoji_id="5199428494471221889"),
        "\n\n",
        "Занятия ведёт Михаил (или Майкл)\n\n",
        CustomEmoji("*️⃣", custom_emoji_id="5229183941998576068"),
        "Занимаемся 2 раза в неделю онлайн, а каждое занятие длится 1 час\n\n",
        "Оплатить можно занятия на 2 или 4 недели вперёд:\n",
        BlockQuote(
            Bold("4 занятия (2 недели)"),
            CustomEmoji("➡️", custom_emoji_id="5231353755181545862"),
            Bold(" 10 000 ₽"),
            "\n",
            Bold("8 занятий (1 месяц)"),
            CustomEmoji("➡️", custom_emoji_id="5231353755181545862"),
            Bold(" 20 000 ₽"),
        ),
        "\n\n",
        CustomEmoji("*️⃣", custom_emoji_id="5229183941998576068"),
        Bold("Самый вайб:"), "\n",
        "По системе", Bold("«Плати за 2, получай 7»"), "ты можешь бесплатно "
        "посещать ещё 5 активностей в неделю в период обучения:\n\n",
        CustomEmoji("🔵", custom_emoji_id="5350750757928855553"),
        "3 клуба 30-36 / грамматических клуба\n",
        CustomEmoji("🔵", custom_emoji_id="5350750757928855553"),
        "1 speaking club\n",
        CustomEmoji("🔵", custom_emoji_id="5350750757928855553"),
        "1 reading club\n",
        CustomEmoji("🔵", custom_emoji_id="5350750757928855553"),
        "пробник ДВИ каждый месяц\n\n",
        "Если уже чувствуешь, что это твоё, ",
        Bold("забирай место в группе или начни с бесплатного пробного занятия "),
        CustomEmoji("💙", custom_emoji_id="5199890066016588263"),
    )
    return text


def get_olympics_course_info_message() -> Text:
    """Текст прайса подготовки к олимпиадам (подпись к медиа-группе)"""
    text = Text(
        "Bestie, подготовку к олимпиадам мы выделили в отдельный формат\n\n",
        "Стоимость занятий - ", Bold("1500 ₽ / 2 часа"), " в группах до 10 students ",
        "с одинаковым уровнем знаний",
        CustomEmoji("🍒", custom_emoji_id="5323767600121945346"),
        "\n\n",
        "Занятия ведёт eng mom Соня (и её собачка Тэффи)",
        CustomEmoji("🐶", custom_emoji_id="5357209692957338380"),
        "\n\n",
        CustomEmoji("*️⃣", custom_emoji_id="5229183941998576068"),
        "Занимаемся 2 раза в неделю онлайн, а каждое занятие длится 2 часа\n\n",
        "Оплатить можно занятия на 2 или 4 недели вперёд:\n",
        BlockQuote(
            Bold("4 занятия (2 недели)"),
            CustomEmoji("➡️", custom_emoji_id="5231353755181545862"),
            Bold(" 6000 ₽"),
            "\n",
            Bold("8 занятий (1 месяц)"),
            CustomEmoji("➡️", custom_emoji_id="5231353755181545862"),
            Bold(" 12 000 ₽"),
        ),
        "\n\n",
        CustomEmoji("*️⃣", custom_emoji_id="5229183941998576068"),
        Bold("Самый вайб:"), "\n",
        "По системе ", Bold("«Плати за 2, получай 7»"), " ты можешь бесплатно ",
        "посещать ещё 5 активностей в неделю в период обучения:\n\n",
        CustomEmoji("🩷", custom_emoji_id="5348256163613927358"),
        "3 клуба 30-36 / грамматических клуба\n",
        CustomEmoji("🩷", custom_emoji_id="5348256163613927358"),
        "1 speaking club\n",
        CustomEmoji("🩷", custom_emoji_id="5348256163613927358"),
        "1 reading club\n",
        CustomEmoji("🩷", custom_emoji_id="5348256163613927358"),
        "проверка всех письменных работ экспертами\n\n",
        "Если уже чувствуешь, что это твоё, ",
        Bold("забирай место в группе или начни с бесплатного пробного занятия "),
        CustomEmoji("🗝", custom_emoji_id="5420637112854681060"),
    )
    return text


def get_payment_confirmation_message() -> Text:
    """Формирует текст сообщения подтверждения заявки на оплату (для 2 недель и 1 месяца)"""
    text = Text(
        Bold("Yaaay, bestik, заявка получена "),
        CustomEmoji("🎀", custom_emoji_id="5199582550653163382"),
        "\n\n",
        "Совсем скоро наш менеджер напишет тебе с аккаунта @ladadada_boss\n\n",
        Bold("Проверь, пожалуйста, что личные сообщения открыты"),
        "\n\n",
        "А пока можешь погулять по боту: скачать полезные материалы, посмотреть отзывы, "
        "изучить additional activities ",
        CustomEmoji("❤️", custom_emoji_id="5199677078588382034"),
        "\n\n",
        "Для этого нажми кнопку «Домой». Твоя заявка никуда не потеряется ",
        CustomEmoji("🍪", custom_emoji_id="5231456735612400746"),
    )
    return text


def get_about_school_message() -> Text:
    """Формирует текст сообщения 'О школе'"""
    text = Text(
        Bold("Мы - ladada_english "),
        CustomEmoji("🎀", custom_emoji_id="5199582550653163382"),
        "\n\n",
        "Подготовим тебя к ЕГЭ на",
        CustomEmoji("8️⃣", custom_emoji_id="5233731599400468187"),
        CustomEmoji("5️⃣", custom_emoji_id="5233620226603515410"),
        "+, а ещё поможем с олимпиадами, ДВИ и ОГЭ ",
        CustomEmoji("🫂", custom_emoji_id="5418240555463259791"),
        "\n\n",
        "Наши eng moms объясняют сложное простым языком, составляют стратегию поступления "
        "и поддерживают на каждом этапе, без вебинаров и кураторов\n\n",
        "А ещё у нас есть куча активностей ",
        CustomEmoji("➡️", custom_emoji_id="5231353755181545862"),
        " читай в карточках\n\n",
        Bold("Начинай с бесплатного пробного занятия и становись одной из ladadagirls "),
        CustomEmoji("❤️", custom_emoji_id="5199677078588382034"),
    )
    return text


def get_teachers_list_message() -> str:
    """Формирует текст сообщения со списком преподавателей"""
    message = (
        "<b>Выбери своего преподавателя</b> 👩‍🏫\n\n"
        "У нас работают только лучшие eng moms, которые прошли строгий отбор\n\n"
        "Выбери преподавателя, чтобы узнать о нём больше:"
    )
    return message


async def _safe_delete_message(message: Message) -> None:
    try:
        await message.delete()
    except Exception as e:
        logger.warning("Не удалось удалить сообщение: %s", e)


async def _delete_review_keyboard_and_photo(message: Message) -> None:
    """Карточка отзыва: одно сообщение (фото + клавиатура). Раньше было текст как ответ на фото — тогда удаляем оба."""
    photo_msg = message.reply_to_message
    await _safe_delete_message(message)
    if photo_msg:
        await _safe_delete_message(photo_msg)


async def _send_ege_course_price_album(
    bot,
    chat_id: int,
    *,
    course_back_callback: str = "price_track",
) -> None:
    """Альбом ЕГЭ/ОГЭ + прайс и клавиатура."""
    course_text = get_course_info_message()
    caption_text, caption_entities = course_text.render()
    await media_cache.send_photo_album(
        bot,
        chat_id,
        NEW_PRICE_PHOTOS,
        caption=caption_text,
        caption_entities=caption_entities,
        parse_mode=None,
    )
    await bot.send_message(
        chat_id=chat_id,
        text="Используй кнопки ниже:",
        reply_markup=get_ege_tariff_keyboard(course_back_callback),
        parse_mode="HTML",
    )


async def _send_dvi_course_price_album(
    bot,
    chat_id: int,
    *,
    track_back_callback: str = "price_track",
) -> None:
    """Альбом ДВИ + текст и отдельная клавиатура заявок."""
    dvi_text = get_dvi_course_info_message()
    caption_text, caption_entities = dvi_text.render()
    await media_cache.send_photo_album(
        bot,
        chat_id,
        [DVI_PHOTO_1, DVI_PHOTO_2],
        caption=caption_text,
        caption_entities=caption_entities,
        parse_mode=None,
    )
    await bot.send_message(
        chat_id=chat_id,
        text="Используй кнопки ниже:",
        reply_markup=get_dvi_course_info_keyboard(track_back_callback=track_back_callback),
        parse_mode="HTML",
    )


async def _send_olympics_course_price_album(
    bot,
    chat_id: int,
    *,
    track_back_callback: str = "price_track",
) -> None:
    """Альбом олимпиад + текст и отдельная клавиатура заявок."""
    olympics_text = get_olympics_course_info_message()
    caption_text, caption_entities = olympics_text.render()
    await media_cache.send_photo_album(
        bot,
        chat_id,
        OLYMPICS_PHOTOS,
        caption=caption_text,
        caption_entities=caption_entities,
        parse_mode=None,
    )
    await bot.send_message(
        chat_id=chat_id,
        text="Используй кнопки ниже:",
        reply_markup=get_olympics_course_info_keyboard(track_back_callback=track_back_callback),
        parse_mode="HTML",
    )


async def send_welcome_screen(bot, chat_id: int) -> None:
    """Приветственное видео, подпись и главная клавиатура (как при /start)."""
    start_text = get_start_message()
    text_value, entities_value = start_text.render()
    await media_cache.send_video(
        bot,
        chat_id,
        WELCOME_VIDEO_PATH,
        width=VIDEO_SEND_WIDTH,
        height=VIDEO_SEND_HEIGHT,
        caption=text_value,
        caption_entities=entities_value,
        parse_mode=None,
        reply_markup=get_start_keyboard(),
    )


def get_schedule_format_message() -> Text:
    """Формирует текст сообщения о расписании и формате обучения"""
    text = Text(
        Bold("Как проходят занятия в ladada_eng? "),
        CustomEmoji("🎀", custom_emoji_id="5199582550653163382"),
        "\n\n",
        "Мы собираем ", Bold("мини-группы по 6-7 человек"),
        " с похожими целями и уровнем, а ", Bold("расписание подбираем с преподавателем после набора группы "),
        CustomEmoji("❤️", custom_emoji_id="5199677078588382034"),
        "\n\n",
        "Не используем шаблонные программы, а ", Bold("составляем уроки под конкретную группу:"),
        " с учётом сроков, слабых мест и текущего уровня\n\n",
        "Нам правда важен твой результат, поэтому ", Bold("каждая ladadagirl получает внимание и обратную связь "),
        CustomEmoji("🐰", custom_emoji_id="5255820401455426357"),
        "\n\n",
        CustomEmoji("*️⃣", custom_emoji_id="5229183941998576068"),
        Bold(" Формат занятий и дополнительные активности смотри на карточках"),
        "\n\nP. S. На некоторые из них можно попасть даже без обучения в группе\n\n",
        Bold("Если коротко: мы подстраиваем обучение под тебя, а не наоборот "),
        "\n\n",
        Bold("Запишись на пробное занятие и набери заветные"),
        CustomEmoji("8️⃣", custom_emoji_id="5233731599400468187"),
        CustomEmoji("5️⃣", custom_emoji_id="5233620226603515410"),
        Bold("+"),
    )
    return text


def get_study_platform_message() -> Text:
    """Формирует текст сообщения об учебной платформе (подпись к медиа-группе)"""
    pink = CustomEmoji("🩷", custom_emoji_id="5350487386239296216")
    rabbit = CustomEmoji("🐇", custom_emoji_id="5323694053101968255")
    ribbon = CustomEmoji("🎀", custom_emoji_id="5269453014199994463")
    text = Text(
        "У нас есть ", Bold("собственная учебная платформа"), " где всё для подготовки собрано в одном месте:\n\n",
        pink, " ", "уроки на сегодня (они там же и проводятся)", "\n",
        pink, " ", "расписание на месяц и остаток оплаченных уроков", "\n",
        pink, " ", "учебные материалы", "\n",
        pink, " ", "чат с eng mom", "\n",
        pink, " ", "AI-тренер, который даёт задания по пройденным темам", "\n",
        pink, " ", "и игра с котиками, которые собирают твои баллы ЕГЭ ", rabbit, "\n\n",
        Bold("Это очень удобно: зашла в личный кабинет "), CustomEmoji("➡️", custom_emoji_id="5231353755181545862"), Bold(" всё нужное уже там "), ribbon,
    )
    return text


def get_additional_activities_message() -> Text:
    """Формирует текст сообщения о дополнительных активностях"""
    text = Text(
        "Для всех students мы организуем ", Bold("бесплатные активности 5 раз в неделю:"),
        "\n\n",
        CustomEmoji("🩷", custom_emoji_id="5350487386239296216"), " reading club\n",
        CustomEmoji("🩷", custom_emoji_id="5350487386239296216"), " клуб 30-36\n",
        CustomEmoji("🩷", custom_emoji_id="5350487386239296216"), " грамматический клуб\n",
        CustomEmoji("🩷", custom_emoji_id="5350487386239296216"), " лекции и встречи (их мы анонсируем в нашем тгк @ladada_eng)\n",
        CustomEmoji("🩷", custom_emoji_id="5350487386239296216"), " speaking club\n",
        CustomEmoji("🩷", custom_emoji_id="5350487386239296216"), " пробники с экспертами\n\n",
        CustomEmoji("*️⃣", custom_emoji_id="5229183941998576068"),
        " На спикинги и пробники может записаться не только ladadagirl",
    )
    return text


def get_speaking_club_message() -> Text:
    """Формирует текст сообщения о спикинг клабе"""
    text = Text(
        Bold("Speaking Club в ladada_eng с носителем "),
        CustomEmoji("🎀", custom_emoji_id="5199582550653163382"),
        "\n\n3000 ₽/месяц (4 встречи)", "\n\n",
        CustomEmoji("*️⃣", custom_emoji_id="5229183941998576068"),
        Bold(" Для учениц ladada_eng - бесплатно "),
        CustomEmoji("🩷", custom_emoji_id="5350665365389071796"),
        "\n\nЭто регулярная практика, где ты можешь быть собой и наконец начать говорить на английском ",
        CustomEmoji("🐰", custom_emoji_id="5255820401455426357"),
        "\n\nЗа 24 часа до встречи мы отправляем материалы для подготовки, а на самом спикинге обсуждаем тему и делимся", 
        " на мини-группы по уровню с преподавателем, который помогает формулировать мысли\n\n",
        CustomEmoji("🎀", custom_emoji_id="5199582550653163382"),
        Bold(" Записывайся, если хочешь спикать "),
        CustomEmoji("⬇️", custom_emoji_id="5231486087418905312"),
    )
    return text


def get_mock_exams_message() -> Text:
    """Формирует текст сообщения о пробниках с экспертами"""
    text = Text(
        Bold("Пробный экзамен в ladada_eng - 2000 ₽"), "\n\n",
        CustomEmoji("*️⃣", custom_emoji_id="5229183941998576068"),
        " Для учениц ladada_eng пробники ", Bold("бесплатные"),
        "\n\n",
        Bold("Тут мы полностью имитируем ЕГЭ:"),
        "\n\n",
        CustomEmoji("🩷", custom_emoji_id="5350487386239296216"),
        " устная + письменная часть с проверкой реальным экспертом ЕГЭ\n",
        CustomEmoji("🩷", custom_emoji_id="5350487386239296216"),
        " тестовая часть с прокторингом\n",
        CustomEmoji("🩷", custom_emoji_id="5350487386239296216"),
        " разбор типичных ошибок\n",
        CustomEmoji("🩷", custom_emoji_id="5350487386239296216"),
        " понимание структуры экзамена\n",
        CustomEmoji("🩷", custom_emoji_id="5350487386239296216"),
        " обучение правильному заполнению бланков\n\n",
        Bold("Записывайся, если хочешь понять свой реальный уровень и готовность к экзамену "),
        CustomEmoji("⬇️", custom_emoji_id="5231486087418905312"),
    )
    return text


def get_reviews_message() -> Text:
    """Формирует текст сообщения об отзывах"""
    text = Text(
        "Мы можем долго рассказывать, какие мы cute and cool, но ",
        "лучше покажем, что говорят ladadagirls ",
        CustomEmoji("🎀", custom_emoji_id="5199582550653163382"),
        "\n\n",
        Bold("Читай реальные отзывы учениц"),
        "\n",
        CustomEmoji("⬇️", custom_emoji_id="5231486087418905312"),
        CustomEmoji("⬇️", custom_emoji_id="5231486087418905312"),
        CustomEmoji("⬇️", custom_emoji_id="5231486087418905312"),
    )
    return text


def get_free_materials_message() -> Text:
    """Формирует текст сообщения о бесплатных материалах"""
    text = Text(
        "Собрали для тебя ", Bold("материалы, за которые обычно платят."),
        " Эстетичные, понятные и реально полезные",
        CustomEmoji("📚", custom_emoji_id="5350407701711053269"),
        "\n\n",
        CustomEmoji("🔴", custom_emoji_id="5350663780546142388"),
        "если путаешься во всех presents, pasts, futures\n",
        CustomEmoji("🔴", custom_emoji_id="5350663780546142388"),
        "если хочется больше практики\n",
        CustomEmoji("🔴", custom_emoji_id="5350663780546142388"),
        "если твоя цель ",
        CustomEmoji("8️⃣", custom_emoji_id="5233731599400468187"),
        CustomEmoji("5️⃣", custom_emoji_id="5233620226603515410"), "+\n\n",
        "- скачивай материалы от english moms и пользуйся ",
        CustomEmoji("❤️", custom_emoji_id="5199677078588382034"),
        "\n\n",
        "А ещё у нас есть ", Bold("AI-бот, который сгенерирует для тебя бесконечные задания"), " по нужной теме", 
        "\n\n",
        CustomEmoji("*️⃣", custom_emoji_id="5229183941998576068"),
        Bold(" Помни, что результат = полезные материалы + чёткая система подготовки. Поэтому советуем начать сразу с бесплатного пробного урока"),
        "\n\n",
        "Let's get your dream score, bestik 🫶🏼"
    )
    return text


def get_text_message_about_teacher(teacher_name_instrumental: str) -> Text:
    """Формирует текст сообщения о конкретном преподавателе для записи на занятие"""
    text = Text(
        f"По кнопкам ниже ты можешь записаться на бесплатное занятие с {teacher_name_instrumental} или сразу купить курс занятий ",
        CustomEmoji("⬇️", custom_emoji_id="5231486087418905312"),
        CustomEmoji("⬇️", custom_emoji_id="5231486087418905312"),
        CustomEmoji("⬇️", custom_emoji_id="5231486087418905312"),
    )

    return text


def get_material_info_message(material_key: str) -> str:
    """Формирует текст сообщения о конкретном материале"""
    material = MATERIALS.get(material_key)
    if not material:
        return "Материал не найден"
    return (
        f"<b>{material['title']}</b> 📚\n\n"
        f"{material['description']}\n\n"
        f"<b>Скачивай и используй для подготовки!</b> ✨"
    )


def _next_review_author_genitive(current_review_id: int) -> str:
    """Имя следующего автора в род. п. (от …) для кнопки навигации."""
    n = len(REVIEWS)
    next_id = (current_review_id % n) + 1
    r = REVIEWS[next_id - 1]
    return r.get("author_genitive_with_university") or r.get("author_genitive") or r["author"]


async def _send_review_photo_message(bot, chat_id: int, review_id: int) -> None:
    """Отзыв: одно сообщение — фото с inline-клавиатурой, без подписи."""
    if review_id < 1 or review_id > len(REVIEWS):
        review_id = 1
    review = REVIEWS[review_id - 1]
    next_author_genitive = _next_review_author_genitive(review_id)
    await media_cache.send_photo(
        bot,
        chat_id,
        review["photo_path"],
        reply_markup=get_review_keyboard(review_id, next_author_genitive, len(REVIEWS)),
    )


async def send_application_to_amo_crm(application: TrialApplication) -> bool:
    """
    Отправка заявки в AMO CRM
    
    TODO: Реализовать интеграцию с AMO CRM
    - Создать контакт в AMO CRM
    - Создать сделку/лид
    - Сохранить ID контакта в application.amo_contact_id
    - Установить application.sent_to_amo = True
    
    Args:
        application: Объект заявки на пробное занятие
        
    Returns:
        bool: True если отправка успешна, False в противном случае
    """
    user = application.user
    is_dvi = application.notes and "ДВИ" in application.notes
    lead_name = (
        f"Пробное ДВИ МГИМО | TG {user.user_id}"
        if is_dvi
        else f"Пробное занятие | TG {user.user_id}"
    )
    lead_price = 0
    lead_note = application.notes or "Заявка на бесплатное пробное занятие"

    contact_id, lead_id = _create_amo_lead_with_contact(user, lead_name, lead_price, lead_note)
    if not contact_id or not lead_id:
        return False

    application.amo_contact_id = str(contact_id)
    application.sent_to_amo = True
    application.save()
    logger.info(f"Заявка {application.id} отправлена в AMO CRM: contact_id={contact_id}, lead_id={lead_id}")
    return True


async def send_payment_application_to_amo_crm(application: PaymentApplication) -> bool:
    """
    Отправка заявки на оплату в AMO CRM
    
    TODO: Реализовать интеграцию с AMO CRM
    - Создать/обновить контакт в AMO CRM
    - Создать сделку с указанием периода и суммы
    - Сохранить ID контакта в application.amo_contact_id
    - Сохранить ID сделки в application.amo_deal_id
    - Установить application.sent_to_amo = True
    
    Args:
        application: Объект заявки на оплату курса
        
    Returns:
        bool: True если отправка успешна, False в противном случае
    """
    user = application.user
    period_label = "2 недели" if application.period == "2_weeks" else "1 месяц"
    notes = application.notes or ""
    is_dvi = "ДВИ" in notes or application.course == "dvi"
    is_ege = "ЕГЭ" in notes or application.course == "ege"
    is_olympics = "Олимпиад" in notes or application.course == "olympics"
    paid_mark = "ОПЛАЧЕНО через Т‑Банк. "
    if is_dvi:
        lead_name = f"Оплата ДВИ МГИМО ({period_label}) | TG {user.user_id}"
        lead_note = (
            f"{paid_mark}ДВИ МГИМО. Период: {period_label}. Сумма: {application.amount} RUB. "
            f"OrderId={application.order_id}."
        )
    elif is_ege:
        tariff_part = notes.replace("ЕГЭ", "").strip() or "basic"
        lead_name = f"Оплата ЕГЭ {tariff_part} ({period_label}) | TG {user.user_id}"
        lead_note = (
            f"{paid_mark}ЕГЭ ({tariff_part}). Период: {period_label}. "
            f"Сумма: {application.amount} RUB. OrderId={application.order_id}."
        )
    elif is_olympics:
        lead_name = f"Оплата олимпиад ({period_label}) | TG {user.user_id}"
        lead_note = (
            f"{paid_mark}Олимпиады. Период: {period_label}. Сумма: {application.amount} RUB. "
            f"OrderId={application.order_id}."
        )
    else:
        lead_name = f"Оплата курса ({period_label}) | TG {user.user_id}"
        lead_note = (
            f"{paid_mark}Период: {period_label}. Сумма: {application.amount} RUB. "
            f"OrderId={application.order_id}."
        )

    contact_id, lead_id = _create_amo_lead_with_contact(user, lead_name, application.amount, lead_note)
    if not contact_id or not lead_id:
        return False

    application.amo_contact_id = str(contact_id)
    application.amo_deal_id = str(lead_id)
    application.sent_to_amo = True
    application.save()
    logger.info(
        f"Заявка на оплату {application.id} отправлена в AMO CRM: "
        f"contact_id={contact_id}, lead_id={lead_id}"
    )
    return True


async def send_speaking_club_application_to_amo_crm(application: SpeakingClubApplication) -> bool:
    """
    Отправка заявки на спикинг клаб в AMO CRM
    
    TODO: Реализовать интеграцию с AMO CRM
    - Создать/обновить контакт в AMO CRM
    - Создать сделку/лид для спикинг клаба
    - Сохранить ID контакта в application.amo_contact_id
    - Сохранить ID сделки в application.amo_deal_id
    - Установить application.sent_to_amo = True
    
    Args:
        application: Объект заявки на спикинг клаб
        
    Returns:
        bool: True если отправка успешна, False в противном случае
    """
    user = application.user
    lead_name = f"Спикинг-клаб | TG {user.user_id}"
    lead_note = application.notes or "Заявка на speaking club (3000 RUB/месяц)"

    contact_id, lead_id = _create_amo_lead_with_contact(user, lead_name, 3000, lead_note)
    if not contact_id or not lead_id:
        return False

    application.amo_contact_id = str(contact_id)
    application.amo_deal_id = str(lead_id)
    application.sent_to_amo = True
    application.save()
    logger.info(
        f"Заявка на speaking club {application.id} отправлена в AMO CRM: "
        f"contact_id={contact_id}, lead_id={lead_id}"
    )
    return True


async def send_mock_exam_application_to_amo_crm(application: MockExamApplication) -> bool:
    """
    Отправка заявки на пробник с экспертами в AMO CRM
    
    TODO: Реализовать интеграцию с AMO CRM
    - Создать/обновить контакт в AMO CRM
    - Создать сделку/лид для пробника с экспертами
    - Сохранить ID контакта в application.amo_contact_id
    - Сохранить ID сделки в application.amo_deal_id
    - Установить application.sent_to_amo = True
    
    Args:
        application: Объект заявки на пробник с экспертами
        
    Returns:
        bool: True если отправка успешна, False в противном случае
    """
    user = application.user
    lead_name = f"Пробник с экспертами | TG {user.user_id}"
    lead_note = application.notes or "Заявка на пробный экзамен с экспертами (2000 RUB)"

    contact_id, lead_id = _create_amo_lead_with_contact(user, lead_name, 2000, lead_note)
    if not contact_id or not lead_id:
        return False

    application.amo_contact_id = str(contact_id)
    application.amo_deal_id = str(lead_id)
    application.sent_to_amo = True
    application.save()
    logger.info(
        f"Заявка на пробник {application.id} отправлена в AMO CRM: "
        f"contact_id={contact_id}, lead_id={lead_id}"
    )
    return True


async def _parallel_crm_and_google_sheet(crm_coro, row: list) -> None:
    """Отправка в AMO CRM и запись строки в Google Таблицу параллельно."""
    results = await asyncio.gather(
        crm_coro,
        append_sheet_row_async(row),
        return_exceptions=True,
    )
    for label, res in zip(("amo_crm", "google_sheets"), results):
        if isinstance(res, BaseException):
            logger.error(
                "%s: сбой при обработке заявки: %s",
                label,
                res,
                exc_info=res,
            )


def _decode_jwt_payload(jwt_token: str) -> dict:
    """Декодирует payload JWT без проверки подписи для чтения api_domain."""
    if not jwt_token or "." not in jwt_token:
        return {}
    try:
        payload_b64 = jwt_token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8")
        return json.loads(payload_json)
    except Exception:
        return {}


def _amo_api_base_url() -> str:
    explicit_url = (amo_crm_secrets.AMO_BASE_URL or "").strip()
    if explicit_url:
        return explicit_url.rstrip("/")

    subdomain = (amo_crm_secrets.AMO_SUBDOMAIN or "").strip()
    if subdomain:
        return f"https://{subdomain}.amocrm.ru"

    token = amo_crm_secrets.ACCESS_TOKEN
    payload = _decode_jwt_payload(token or "")
    api_domain = payload.get("api_domain")
    if api_domain:
        return f"https://{api_domain}"
    return "https://api.amocrm.ru"


def _build_contact_name(user: User) -> str:
    full_name = " ".join(filter(None, [user.first_name, user.last_name])).strip()
    if full_name and user.username:
        return f"{full_name} (@{user.username})"
    return full_name or (user.username and f"@{user.username}") or f"Telegram ID {user.user_id}"


def _build_telegram_profile_reference(user: User) -> str:
    if user.username:
        return f"https://t.me/{user.username}"
    return f"tg://user?id={user.user_id}"


def _refresh_amo_access_token() -> bool:
    refresh_token = amo_crm_secrets.REFRESH_TOKEN
    client_id = amo_crm_secrets.CRM_ID
    client_secret = amo_crm_secrets.SECRET_KEY
    if not refresh_token or not client_id or not client_secret:
        return False

    url = f"{_amo_api_base_url()}/oauth2/access_token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    req = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception as err:
        logger.error(f"AMO CRM token refresh failed: {err}")
        return False

    new_access = body.get("access_token")
    new_refresh = body.get("refresh_token")
    if not new_access:
        logger.error(f"AMO CRM token refresh response invalid: {body}")
        return False

    amo_crm_secrets.ACCESS_TOKEN = new_access
    if new_refresh:
        amo_crm_secrets.REFRESH_TOKEN = new_refresh
    logger.info("AMO CRM access_token обновлен через refresh_token")
    return True


def _create_amo_lead_with_contact(user: User, lead_name: str, price: int, note: str) -> tuple[str | None, str | None]:
    token = amo_crm_secrets.ACCESS_TOKEN
    if not token:
        logger.error("AMO CRM: ACCESS_TOKEN не задан")
        return None, None

    url = f"{_amo_api_base_url()}/api/v4/leads/complex"
    contact_name = _build_contact_name(user)

    lead_parts = [lead_name]
    lead_parts.append(_build_telegram_profile_reference(user))
    if note:
        lead_parts.append(note[:80])

    payload = [
        {
            "name": " | ".join(lead_parts),
            "price": int(price or 0),
            "_embedded": {
                "contacts": [
                    {
                        "name": contact_name,
                    }
                ]
            },
        }
    ]

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            response_body = response.read().decode("utf-8")
            parsed = json.loads(response_body)
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="ignore") if err.fp else ""
        if err.code == 401 and _refresh_amo_access_token():
            token = amo_crm_secrets.ACCESS_TOKEN
            retry_req = urllib.request.Request(
                url=url,
                data=data,
                method="POST",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(retry_req, timeout=15) as response:
                    response_body = response.read().decode("utf-8")
                    parsed = json.loads(response_body)
            except urllib.error.HTTPError as retry_err:
                retry_body = retry_err.read().decode("utf-8", errors="ignore") if retry_err.fp else ""
                logger.error(f"AMO CRM HTTP error {retry_err.code}: {retry_body}")
                return None, None
            except Exception as retry_err:
                logger.error(f"AMO CRM request failed after refresh: {retry_err}")
                return None, None
        else:
            logger.error(f"AMO CRM HTTP error {err.code}: {body}")
            return None, None
    except Exception as err:
        logger.error(f"AMO CRM request failed: {err}")
        return None, None

    if isinstance(parsed, list) and parsed:
        first = parsed[0]
        lead_id = first.get("id")
        contact_id = first.get("contact_id")
        return str(contact_id) if contact_id else None, str(lead_id) if lead_id else None

    leads = parsed.get("_embedded", {}).get("leads", [])
    if leads:
        lead = leads[0]
        lead_id = lead.get("id")
        contacts = lead.get("_embedded", {}).get("contacts", [])
        contact_id = contacts[0].get("id") if contacts else None
        return str(contact_id) if contact_id else None, str(lead_id) if lead_id else None

    logger.error(f"AMO CRM: unexpected response format: {parsed}")
    return None, None


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    # Сохранение или обновление пользователя в БД
    user, created = User.get_or_create(
        user_id=user_id,
        defaults={
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    )

    # Если пользователь уже существует, обновляем информацию
    if not created:
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.updated_at = datetime.now()
        user.save()

    # Отправка приветственного сообщения с видео и кнопками
    # Проверка доступа к набору эмодзи (закомментировано)
    # logger.info("=== Проверка доступа к набору эмодзи ===")
    # try:
    #     sticker_set = await message.bot.get_sticker_set(name="ladadaeng")
    #     logger.info(f"✅ Набор 'ladadaeng' доступен боту!")
    #     logger.info(f"   Название: {sticker_set.title}")
    #     logger.info(f"   Тип: {sticker_set.sticker_type}")
    #     logger.info(f"   Количество стикеров: {len(sticker_set.stickers)}")
    #     
    #     # Проверяем, есть ли наш эмодзи в наборе
    #     target_id = "5199582550653163382"
    #     found = any(s.custom_emoji_id == target_id for s in sticker_set.stickers if s.custom_emoji_id)
    #     logger.info(f"   Эмодзи {target_id} в наборе: {'Да' if found else 'Нет'}")
    #     
    # except Exception as e:
    #     logger.error(f"❌ Бот НЕ имеет доступа к набору 'ladadaeng': {e}")
    #     logger.error("   Это означает, что бот не может использовать эмодзи из этого набора в сообщениях!")
    #     logger.error("   Решение: используйте эмодзи из публичных наборов Telegram Premium")
    
    # Тест отправки одного эмодзи (закомментировано)
    # logger.info("=== Тест отправки одного эмодзи ===")
    # try:
    #     from aiogram.utils.formatting import Text as TestText, CustomEmoji as TestCustomEmoji
    #     
    #     test_text = TestText("Тест: ", TestCustomEmoji("🎀", custom_emoji_id="5199582550653163382"))
    #     test_text_value, test_entities_value = test_text.render()
    #     
    #     # Логирование перед отправкой
    #     logger.info(f"=== Что отправляется в API ===")
    #     logger.info(f"Текст: '{test_text_value}'")
    #     logger.info(f"Длина текста: {len(test_text_value)} символов")
    #     logger.info(f"Entities count: {len(test_entities_value)}")
    #     for i, entity in enumerate(test_entities_value):
    #         logger.info(f"  Entity {i+1}: type={entity.type}, "
    #                    f"custom_emoji_id={getattr(entity, 'custom_emoji_id', 'N/A')}, "
    #                    f"offset={entity.offset}, length={entity.length}")
    #         if entity.offset < len(test_text_value):
    #             text_at_pos = test_text_value[entity.offset:entity.offset+entity.length]
    #             logger.info(f"    Текст в позиции: '{text_at_pos}'")
    #     
    #     test_msg = await message.answer(
    #         text=test_text_value,
    #         entities=test_entities_value,
    #         parse_mode=None
    #     )
    #     
    #     # Логирование после отправки
    #     logger.info(f"=== Проверка отправленного сообщения ===")
    #     logger.info(f"✅ Тестовое сообщение отправлено! ID: {test_msg.message_id}")
    #     logger.info(f"Отправленное сообщение text: '{test_msg.text}'")
    #     logger.info(f"Отправленное сообщение entities count: {len(test_msg.entities) if test_msg.entities else 0}")
    #     
    #     if test_msg.entities:
    #         for i, entity in enumerate(test_msg.entities):
    #             logger.info(f"  Entity {i+1}: type={entity.type}")
    #             if entity.type == MessageEntityType.CUSTOM_EMOJI:
    #                 logger.info(f"    Custom emoji: custom_emoji_id={entity.custom_emoji_id}, "
    #                            f"offset={entity.offset}, length={entity.length}")
    #                 # Проверяем текст в этой позиции
    #                 if entity.offset < len(test_msg.text):
    #                     text_at_pos = test_msg.text[entity.offset:entity.offset+entity.length]
    #                     logger.info(f"    Текст в позиции: '{text_at_pos}'")
    #     else:
    #         logger.warning("⚠️ Entities НЕ вернулись в ответе! Это означает, что они не были переданы в API")
    #     
    #     logger.info(f"   Проверьте, отображается ли премиум-эмодзи в этом сообщении")
    # except Exception as e:
    #     logger.error(f"❌ Ошибка при отправке тестового сообщения: {e}")
    #     if "Bad Request" in str(e) or "invalid" in str(e).lower():
    #         logger.error("   Вероятно, бот не имеет доступа к этому эмодзи!")
    
    # Логирование для отладки премиум-эмодзи (закомментировано)
    # logger.info(f"=== Отправка видео с caption ===")
    # start_text = get_start_message()
    # text_value, entities_value = start_text.render()
    # logger.info(f"Caption length: {len(text_value)} символов")
    # logger.info(f"Caption preview: {text_value[:100]}...")
    # logger.info(f"Entities count: {len(entities_value)}")
    # logger.info(f"Parse mode: None")
    # 
    # # Логируем все entities с custom_emoji
    # custom_emoji_entities = [e for e in entities_value if e.type == MessageEntityType.CUSTOM_EMOJI]
    # logger.info(f"Custom emoji entities count: {len(custom_emoji_entities)}")
    # 
    # for i, entity in enumerate(custom_emoji_entities[:5]):  # Первые 5 для примера
    #     logger.info(f"  Entity {i+1}: type={entity.type}, custom_emoji_id={entity.custom_emoji_id}, "
    #                f"offset={entity.offset}, length={entity.length}")
    #     # Показываем текст в этой позиции
    #     if entity.offset < len(text_value):
    #         text_at_offset = text_value[entity.offset:entity.offset+entity.length]
    #         logger.info(f"    Text at position: '{text_at_offset}'")

    await send_welcome_screen(message.bot, message.chat.id)


@router.callback_query(F.data == "trial_lesson")
async def callback_trial_lesson(callback: CallbackQuery):
    """Обработчик кнопки 'Записаться на бесплатное пробное занятие'"""
    # Отвечаем на callback, чтобы убрать индикатор загрузки
    await callback.answer()
    
    # Проверяем, что сообщение существует
    if callback.message:
        # Удаляем старое сообщение
        await callback.message.delete()
        
        # Получаем текст и entities для caption
        trial_text = get_trial_lesson_message()
        caption_text, caption_entities = trial_text.render()
        
        await media_cache.send_photo_album(
            callback.message.bot,
            callback.message.chat.id,
            [
                "all_media/TrialFirstPhoto.jpg",
                "all_media/TrialSecondPhoto.jpg",
            ],
            caption=caption_text,
            caption_entities=caption_entities,
            parse_mode=None,
        )
        
        # Отправляем сообщение с клавиатурой после медиа-группы
        await callback.message.bot.send_message(
            chat_id=callback.message.chat.id,
            text="Используй кнопки ниже:",
            reply_markup=get_trial_lesson_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "about_school")
async def callback_about_school(callback: CallbackQuery):
    """Обработчик кнопки 'Узнать о школе, занятиях и активностях'"""
    # Отвечаем на callback, чтобы убрать индикатор загрузки
    await callback.answer()
    
    # Проверяем, что сообщение существует
    if callback.message:
        # Удаляем предыдущее сообщение и отправляем медиагруппу
        await callback.message.delete()

        # Получаем текст и entities для caption
        about_school_text = get_about_school_message()
        caption_text, caption_entities = about_school_text.render()

        photo_paths = [
            "all_media/AboutSchoolPhotos/FirstSchoolPhoto.jpg",
            "all_media/AboutSchoolPhotos/SecondSchoolPhoto.jpg",
            "all_media/AboutSchoolPhotos/ThirdSchoolPhoto.jpg",
            "all_media/AboutSchoolPhotos/FourthSchoolPhoto.jpg",
        ]
        await media_cache.send_photo_album(
            callback.message.bot,
            callback.message.chat.id,
            photo_paths,
            caption=caption_text,
            caption_entities=caption_entities,
            parse_mode=None,
        )

        await callback.message.bot.send_message(
            chat_id=callback.message.chat.id,
            text="Используй кнопки ниже:",
            reply_markup=get_about_school_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "schedule_format")
async def callback_schedule_format(callback: CallbackQuery):
    """Обработчик кнопки 'Посмотреть расписание и формат обучения'"""
    await callback.answer()

    if not callback.message:
        return

    await callback.message.delete()

    schedule_text = get_schedule_format_message()
    caption_text, caption_entities = schedule_text.render()

    photo_paths = [
        "all_media/SchedulePhotos/Schedule1.jpg",
        "all_media/SchedulePhotos/Schedule2.jpg",
    ]
    await media_cache.send_photo_album(
        callback.message.bot,
        callback.message.chat.id,
        photo_paths,
        caption=caption_text,
        caption_entities=caption_entities,
        parse_mode=None,
    )

    await callback.message.bot.send_message(
        chat_id=callback.message.chat.id,
        text="Используй кнопки ниже:",
        reply_markup=get_schedule_format_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "study_platform")
async def callback_study_platform(callback: CallbackQuery):
    """Обработчик кнопки 'Посмотреть учебную платформу'"""
    await callback.answer()

    if not callback.message:
        return

    await callback.message.delete()

    platform_text = get_study_platform_message()
    caption_text, caption_entities = platform_text.render()
    await media_cache.send_photo_album(
        callback.message.bot,
        callback.message.chat.id,
        STUDY_PLATFORM_PHOTOS,
        caption=caption_text,
        caption_entities=caption_entities,
        parse_mode=None,
    )

    await callback.message.bot.send_message(
        chat_id=callback.message.chat.id,
        text="Используй кнопки ниже:",
        reply_markup=get_study_platform_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "signup_additional_activities")
async def callback_signup_additional_activities(callback: CallbackQuery):
    """Экран доп. активностей (кнопка в расписании или «Назад» с прайса/спикинга/пробников)."""
    await callback.answer()

    if not callback.message:
        return

    bot = callback.message.bot
    chat_id = callback.message.chat.id
    additional_text = get_additional_activities_message()
    text_value, entities_value = additional_text.render()
    keyboard = get_additional_activities_keyboard()

    try:
        await callback.message.edit_text(
            text=text_value,
            entities=entities_value,
            reply_markup=keyboard,
            parse_mode=None,
        )
    except Exception as e:
        logger.warning(
            "Не удалось вернуть доп. активности через edit_text (отправляем новое сообщение): %s",
            e,
        )
        await _safe_delete_message(callback.message)
        await bot.send_message(
            chat_id=chat_id,
            text=text_value,
            entities=entities_value,
            reply_markup=keyboard,
            parse_mode=None,
        )


@router.callback_query(F.data == "speaking_club_info")
async def callback_speaking_club_info(callback: CallbackQuery):
    """Обработчик кнопки 'Узнать больше о спикинг клабе': видео, затем альбом с текстом."""
    await callback.answer()

    if not callback.message:
        return

    bot = callback.message.bot
    chat_id = callback.message.chat.id
    msg_to_remove = callback.message

    # Сначала отправляем контент, потом удаляем сообщение с кнопками — иначе при любой
    # ошибке (нет файла на сервере, лимит API) пользователь теряет клавиатуру, а в чате
    # остаётся предыдущий альбом «Как проходят занятия…».
    sent_any = False
    try:
        await media_cache.send_video(
            bot,
            chat_id,
            SPEAKING_CLUB_VIDEO_PATH,
            width=SPEAKING_CLUB_VIDEO_WIDTH,
            height=SPEAKING_CLUB_VIDEO_HEIGHT,
            supports_streaming=True,
        )
        sent_any = True

        speaking_text = get_speaking_club_message()
        caption_text, caption_entities = speaking_text.render()
        photo_paths = [
            "all_media/SpeakingMedia/Speaking1.jpg",
            "all_media/SpeakingMedia/Speaking2.jpg",
            "all_media/SpeakingMedia/Speaking3.jpg",
        ]
        await media_cache.send_photo_album(
            bot,
            chat_id,
            photo_paths,
            caption=caption_text,
            caption_entities=caption_entities,
            parse_mode=None,
        )
        sent_any = True

        await bot.send_message(
            chat_id=chat_id,
            text="Используй кнопки ниже:",
            reply_markup=get_speaking_club_keyboard(),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.exception("Ошибка при отправке блока спикинг-клаба: %s", e)
        if sent_any:
            await bot.send_message(
                chat_id=chat_id,
                text="Часть материалов не отправилась. Попробуй ещё раз или напиши нам в поддержку.",
                reply_markup=get_additional_activities_keyboard(),
                parse_mode="HTML",
            )
            await _safe_delete_message(msg_to_remove)
        return

    await _safe_delete_message(msg_to_remove)


@router.callback_query(F.data == "mock_exams_info")
async def callback_mock_exams_info(callback: CallbackQuery):
    """Обработчик кнопки 'Узнать больше о пробниках с экспертами'"""
    # Отвечаем на callback, чтобы убрать индикатор загрузки
    await callback.answer()
    
    # Проверяем, что сообщение существует и доступно для редактирования
    if callback.message:
        # Редактируем сообщение вместо отправки нового
        mock_text = get_mock_exams_message()
        text_value, entities_value = mock_text.render()
        await callback.message.edit_text(
            text=text_value,
            entities=entities_value,
            reply_markup=get_mock_exams_keyboard(),
            parse_mode=None,
        )


@router.callback_query(F.data == "signup_speaking_club")
async def callback_signup_speaking_club(callback: CallbackQuery):
    """Обработчик кнопки 'Записаться на спикинг клаб'"""
    # Отвечаем на callback, чтобы убрать индикатор загрузки
    await callback.answer()
    
    if not callback.message:
        return
    
    user_id = callback.from_user.id
    
    try:
        # Получаем или создаем пользователя
        user = User.get(User.user_id == user_id)
        
        # Создаем заявку на спикинг клаб
        application = SpeakingClubApplication.create(
            user=user,
            created_at=datetime.now()
        )
        
        logger.info(f"Создана заявка на спикинг клаб: {application.id} для пользователя {user_id}")
        
        row = build_row_for_application(application, "speaking_club")
        await _parallel_crm_and_google_sheet(
            send_speaking_club_application_to_amo_crm(application),
            row,
        )
        
        # Редактируем сообщение, показывая подтверждение
        confirmation_text = get_signup_confirmation_message()
        text_value, entities_value = confirmation_text.render()
        await callback.message.edit_text(
            text=text_value,
            entities=entities_value,
            reply_markup=get_signup_confirmation_keyboard(),
            parse_mode=None
        )
        
    except User.DoesNotExist:
        logger.error(f"Пользователь {user_id} не найден в БД")
        await callback.message.edit_text(
            text="Произошла ошибка. Пожалуйста, начните с команды /start",
            reply_markup=get_signup_confirmation_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка при создании заявки на спикинг клаб: {e}")
        await callback.message.edit_text(
            text="Произошла ошибка при обработке заявки. Попробуйте позже.",
            reply_markup=get_signup_confirmation_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "signup_mock_exam")
async def callback_signup_mock_exam(callback: CallbackQuery):
    """Обработчик кнопки 'Записаться на пробник с экспертами'"""
    # Отвечаем на callback, чтобы убрать индикатор загрузки
    await callback.answer()
    
    if not callback.message:
        return
    
    user_id = callback.from_user.id
    
    try:
        # Получаем или создаем пользователя
        user = User.get(User.user_id == user_id)
        
        # Создаем заявку на пробник с экспертами
        application = MockExamApplication.create(
            user=user,
            created_at=datetime.now()
        )
        
        logger.info(f"Создана заявка на пробник с экспертами: {application.id} для пользователя {user_id}")
        
        row = build_row_for_application(application, "mock_exam")
        await _parallel_crm_and_google_sheet(
            send_mock_exam_application_to_amo_crm(application),
            row,
        )
        
        # Редактируем сообщение, показывая подтверждение
        confirmation_text = get_signup_confirmation_message()
        text_value, entities_value = confirmation_text.render()
        await callback.message.edit_text(
            text=text_value,
            entities=entities_value,
            reply_markup=get_signup_confirmation_keyboard(),
            parse_mode=None
        )
        
    except User.DoesNotExist:
        logger.error(f"Пользователь {user_id} не найден в БД")
        await callback.message.edit_text(
            text="Произошла ошибка. Пожалуйста, начните с команды /start",
            reply_markup=get_signup_confirmation_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка при создании заявки на пробник с экспертами: {e}")
        await callback.message.edit_text(
            text="Произошла ошибка при обработке заявки. Попробуйте позже.",
            reply_markup=get_signup_confirmation_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "choose_teacher")
async def callback_choose_teacher(callback: CallbackQuery):
    """Обработчик кнопки 'Выбрать преподавателя'"""
    await callback.answer()

    if not callback.message:
        return

    bot = callback.message.bot
    chat_id = callback.message.chat.id
    text = get_teachers_list_message()
    keyboard = get_teachers_list_keyboard()

    # Карточка преподавателя — видео; edit_text для неё недоступен (см. callback_teacher)
    if callback.message.video:
        await _safe_delete_message(callback.message)
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        return

    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("teacher_"))
async def callback_teacher(callback: CallbackQuery):
    """Обработчик выбора преподавателя и листания ← / → (одно сообщение: видео, подпись, клавиатура)."""
    await callback.answer()

    if not callback.message:
        return

    bot = callback.message.bot
    chat_id = callback.message.chat.id

    try:
        teacher_id = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        logger.error("Ошибка при парсинге teacher_id из callback_data: %s", callback.data)
        await _safe_delete_message(callback.message)
        await bot.send_message(
            chat_id=chat_id,
            text="Произошла ошибка. Попробуйте выбрать преподавателя снова.",
            reply_markup=get_teachers_list_keyboard(),
            parse_mode="HTML",
        )
        return

    if teacher_id < 1 or teacher_id > len(TEACHERS):
        await _safe_delete_message(callback.message)
        await bot.send_message(
            chat_id=chat_id,
            text="Преподаватель не найден. Попробуйте выбрать другого.",
            reply_markup=get_teachers_list_keyboard(),
            parse_mode="HTML",
        )
        return

    teacher = TEACHERS[teacher_id - 1]
    keyboard = get_teacher_keyboard(teacher_id, len(TEACHERS))
    teacher_name_instrumental = teacher.get("name_instrumental", teacher["name"])
    teacher_text = get_text_message_about_teacher(teacher_name_instrumental)
    text_value, entities_value = teacher_text.render()

    # Сначала видео, потом удаление — иначе пустой экран на время upload/кэша
    await media_cache.send_video(
        bot,
        chat_id,
        teacher["video_path"],
        width=VIDEO_SEND_WIDTH,
        height=VIDEO_SEND_HEIGHT,
        caption=text_value,
        caption_entities=entities_value,
        reply_markup=keyboard,
        parse_mode=None,
        supports_streaming=True,
    )
    await _safe_delete_message(callback.message)


@router.callback_query(F.data.startswith("signup_trial_teacher_"))
async def callback_signup_trial_teacher(callback: CallbackQuery):
    """Обработчик кнопки 'Записаться на бесплатное пробное' с конкретным преподавателем"""
    # Отвечаем на callback, чтобы убрать индикатор загрузки
    await callback.answer()
    
    if not callback.message:
        return

    bot = callback.message.bot
    chat_id = callback.message.chat.id

    # Извлекаем ID преподавателя из callback_data
    try:
        teacher_id = int(callback.data.split("_")[-1])
        teacher = TEACHERS[teacher_id - 1] if 1 <= teacher_id <= len(TEACHERS) else None
        
        user_id = callback.from_user.id
        
        # Получаем или создаем пользователя
        user = User.get(User.user_id == user_id)
        
        # Создаем заявку на пробное занятие
        application = TrialApplication.create(
            user=user,
            created_at=datetime.now(),
            notes=f"Выбранный преподаватель: {teacher['name']}" if teacher else None
        )
        
        logger.info(
            f"Создана заявка на пробное занятие: {application.id} "
            f"для пользователя {user_id} с преподавателем {teacher_id}"
        )
        
        row = build_row_for_application(application, "trial")
        await _parallel_crm_and_google_sheet(
            send_application_to_amo_crm(application),
            row,
        )
        
        # Карточка преподавателя — видео; edit_text недоступен, удаляем и шлём текст подтверждения
        confirmation_text = get_signup_confirmation_message()
        text_value, entities_value = confirmation_text.render()
        await _safe_delete_message(callback.message)
        await bot.send_message(
            chat_id=chat_id,
            text=text_value,
            entities=entities_value,
            reply_markup=get_signup_confirmation_keyboard(),
            parse_mode=None,
        )
        
    except User.DoesNotExist:
        logger.error(f"Пользователь {user_id} не найден в БД")
        await _safe_delete_message(callback.message)
        await bot.send_message(
            chat_id=chat_id,
            text="Произошла ошибка. Пожалуйста, начните с команды /start",
            reply_markup=get_signup_confirmation_keyboard(),
            parse_mode="HTML",
        )
    except (ValueError, IndexError) as e:
        logger.error(f"Ошибка при парсинге teacher_id: {e}")
        await _safe_delete_message(callback.message)
        await bot.send_message(
            chat_id=chat_id,
            text="Произошла ошибка. Попробуйте снова.",
            reply_markup=get_signup_confirmation_keyboard(),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Ошибка при создании заявки: {e}")
        await _safe_delete_message(callback.message)
        await bot.send_message(
            chat_id=chat_id,
            text="Произошла ошибка при обработке заявки. Попробуйте позже.",
            reply_markup=get_signup_confirmation_keyboard(),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "signup_trial")
async def callback_signup_trial(callback: CallbackQuery):
    """Обработчик кнопки 'Записаться на бесплатное пробное'"""
    await callback.answer()

    if not callback.message:
        return

    msg = callback.message
    bot = msg.bot
    chat_id = msg.chat.id
    keyboard = get_signup_confirmation_keyboard()

    async def show_signup_result(text: str, entities=None) -> None:
        # Карточка отзыва — фото; edit_text для медиа недоступен
        if msg.photo or msg.video:
            await _safe_delete_message(msg)
            if entities is not None:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    entities=entities,
                    reply_markup=keyboard,
                    parse_mode=None,
                )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
            return
        if entities is not None:
            await msg.edit_text(
                text=text,
                entities=entities,
                reply_markup=keyboard,
                parse_mode=None,
            )
        else:
            await msg.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

    user_id = callback.from_user.id

    try:
        user = User.get(User.user_id == user_id)

        application = TrialApplication.create(
            user=user,
            created_at=datetime.now()
        )

        logger.info(f"Создана заявка на пробное занятие: {application.id} для пользователя {user_id}")

        row = build_row_for_application(application, "trial")
        await _parallel_crm_and_google_sheet(
            send_application_to_amo_crm(application),
            row,
        )

        confirmation_text = get_signup_confirmation_message()
        text_value, entities_value = confirmation_text.render()
        await show_signup_result(text_value, entities_value)

    except User.DoesNotExist:
        logger.error(f"Пользователь {user_id} не найден в БД")
        await show_signup_result(
            "Произошла ошибка. Пожалуйста, начните с команды /start"
        )
    except Exception as e:
        logger.error(f"Ошибка при создании заявки: {e}")
        await show_signup_result(
            "Произошла ошибка при обработке заявки. Попробуйте позже."
        )


@router.callback_query(F.data == "signup_trial_dvi")
async def callback_signup_trial_dvi(callback: CallbackQuery):
    """Пробное занятие по направлению ДВИ МГИМО (отдельная заявка от ЕГЭ/ОГЭ)."""
    await callback.answer()

    if not callback.message:
        return

    msg = callback.message
    bot = msg.bot
    chat_id = msg.chat.id
    keyboard = get_signup_confirmation_keyboard()

    async def show_signup_result(text: str, entities=None) -> None:
        if msg.photo or msg.video:
            await _safe_delete_message(msg)
            if entities is not None:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    entities=entities,
                    reply_markup=keyboard,
                    parse_mode=None,
                )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
            return
        if entities is not None:
            await msg.edit_text(
                text=text,
                entities=entities,
                reply_markup=keyboard,
                parse_mode=None,
            )
        else:
            await msg.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

    user_id = callback.from_user.id

    try:
        user = User.get(User.user_id == user_id)

        application = TrialApplication.create(
            user=user,
            created_at=datetime.now(),
            notes="ДВИ МГИМО: бесплатное пробное занятие",
        )

        logger.info(
            "Создана заявка на пробное ДВИ: %s для пользователя %s",
            application.id,
            user_id,
        )

        row = build_row_for_application(application, "trial")
        await _parallel_crm_and_google_sheet(
            send_application_to_amo_crm(application),
            row,
        )

        confirmation_text = get_signup_confirmation_message()
        text_value, entities_value = confirmation_text.render()
        await show_signup_result(text_value, entities_value)

    except User.DoesNotExist:
        logger.error("Пользователь %s не найден в БД", user_id)
        await show_signup_result("Произошла ошибка. Пожалуйста, начните с команды /start")
    except Exception as e:
        logger.error("Ошибка при создании заявки на пробное ДВИ: %s", e)
        await show_signup_result("Произошла ошибка при обработке заявки. Попробуйте позже.")


@router.callback_query(F.data == "signup_trial_olympics")
async def callback_signup_trial_olympics(callback: CallbackQuery):
    """Пробное занятие по направлению олимпиад (отдельная заявка)."""
    await callback.answer()

    if not callback.message:
        return

    msg = callback.message
    bot = msg.bot
    chat_id = msg.chat.id
    keyboard = get_signup_confirmation_keyboard()

    async def show_signup_result(text: str, entities=None) -> None:
        if msg.photo or msg.video:
            await _safe_delete_message(msg)
            if entities is not None:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    entities=entities,
                    reply_markup=keyboard,
                    parse_mode=None,
                )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
            return
        if entities is not None:
            await msg.edit_text(
                text=text,
                entities=entities,
                reply_markup=keyboard,
                parse_mode=None,
            )
        else:
            await msg.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

    user_id = callback.from_user.id

    try:
        user = User.get(User.user_id == user_id)

        application = TrialApplication.create(
            user=user,
            created_at=datetime.now(),
            notes="Олимпиады: бесплатное пробное занятие",
        )

        logger.info(
            "Создана заявка на пробное по олимпиадам: %s для пользователя %s",
            application.id,
            user_id,
        )

        row = build_row_for_application(application, "trial")
        await _parallel_crm_and_google_sheet(
            send_application_to_amo_crm(application),
            row,
        )

        confirmation_text = get_signup_confirmation_message()
        text_value, entities_value = confirmation_text.render()
        await show_signup_result(text_value, entities_value)

    except User.DoesNotExist:
        logger.error("Пользователь %s не найден в БД", user_id)
        await show_signup_result("Произошла ошибка. Пожалуйста, начните с команды /start")
    except Exception as e:
        logger.error("Ошибка при создании заявки на пробное по олимпиадам: %s", e)
        await show_signup_result("Произошла ошибка при обработке заявки. Попробуйте позже.")


@router.callback_query(F.data == "buy_course_main")
async def callback_buy_course_main(callback: CallbackQuery):
    """Только с главного экрана: сначала выбор направления (ЕГЭ/ОГЭ, ДВИ или олимпиады)."""
    await callback.answer()

    if callback.message:
        await callback.message.delete()
        await callback.message.bot.send_message(
            chat_id=callback.message.chat.id,
            reply_markup=get_price_track_keyboard(show_back=False, main_flow=True),
            **PRICE_TRACK_PROMPT.as_kwargs(),
        )


@router.callback_query(F.data == "buy_course")
async def callback_buy_course(callback: CallbackQuery):
    """«Купить курс» из всех разделов, кроме главного: выбор направления подготовки."""
    await callback.answer()

    if not callback.message:
        return

    await callback.message.delete()
    await callback.message.bot.send_message(
        chat_id=callback.message.chat.id,
        reply_markup=get_price_track_keyboard(
            show_back=True,
            buy_flow=True,
            back_callback="home",
        ),
        **PRICE_TRACK_PROMPT.as_kwargs(),
    )


@router.callback_query(F.data == "price_info")
async def callback_price_info(callback: CallbackQuery):
    """Обработчик кнопки 'Узнать прайс' — сначала ЕГЭ/ОГЭ или ДВИ."""
    await callback.answer()

    if callback.message:
        await callback.message.delete()
        await callback.message.bot.send_message(
            chat_id=callback.message.chat.id,
            reply_markup=get_price_track_keyboard(),
            **PRICE_TRACK_PROMPT.as_kwargs(),
        )


@router.callback_query(F.data == "price_track")
async def callback_price_track(callback: CallbackQuery):
    """Назад с экрана прайса после «Узнать прайс» — выбор направления с кнопкой «Назад»."""
    await callback.answer()

    if not callback.message:
        return

    await callback.message.delete()
    await callback.message.bot.send_message(
        chat_id=callback.message.chat.id,
        reply_markup=get_price_track_keyboard(show_back=True, main_flow=False),
        **PRICE_TRACK_PROMPT.as_kwargs(),
    )


@router.callback_query(F.data == "price_track_main")
async def callback_price_track_main(callback: CallbackQuery):
    """Назад с прайса в ветке «Купить курс» с главного — только «Домой», без дубля «Назад»."""
    await callback.answer()

    if not callback.message:
        return

    await callback.message.delete()
    await callback.message.bot.send_message(
        chat_id=callback.message.chat.id,
        reply_markup=get_price_track_keyboard(show_back=False, main_flow=True),
        **PRICE_TRACK_PROMPT.as_kwargs(),
    )


@router.callback_query(F.data == "price_ege_from_main")
async def callback_price_ege_from_main(callback: CallbackQuery):
    """ЕГЭ/ОГЭ из ветки главного экрана — возврат к выбору без кнопки «Назад»."""
    await callback.answer()

    if not callback.message:
        return

    await callback.message.delete()
    await _send_ege_course_price_album(
        callback.message.bot,
        callback.message.chat.id,
        course_back_callback="price_track_main",
    )


@router.callback_query(F.data == "price_dvi_from_main")
async def callback_price_dvi_from_main(callback: CallbackQuery):
    """ДВИ из ветки главного экрана."""
    await callback.answer()

    if not callback.message:
        return

    await callback.message.delete()
    await _send_dvi_course_price_album(
        callback.message.bot,
        callback.message.chat.id,
        track_back_callback="price_track_main",
    )


@router.callback_query(F.data == "price_olympics_from_main")
async def callback_price_olympics_from_main(callback: CallbackQuery):
    """Олимпиады из ветки главного экрана."""
    await callback.answer()

    if not callback.message:
        return

    await callback.message.delete()
    await _send_olympics_course_price_album(
        callback.message.bot,
        callback.message.chat.id,
        track_back_callback="price_track_main",
    )


@router.callback_query(F.data == "price_ege_oge")
async def callback_price_ege_oge(callback: CallbackQuery):
    """Прайс ЕГЭ/ОГЭ после «Узнать прайс»."""
    await callback.answer()

    if not callback.message:
        return

    await callback.message.delete()
    await _send_ege_course_price_album(callback.message.bot, callback.message.chat.id)


@router.callback_query(F.data == "price_dvi")
async def callback_price_dvi(callback: CallbackQuery):
    """Прайс ДВИ после «Узнать прайс»."""
    await callback.answer()

    if not callback.message:
        return

    await callback.message.delete()
    await _send_dvi_course_price_album(callback.message.bot, callback.message.chat.id)


@router.callback_query(F.data == "price_olympics")
async def callback_price_olympics(callback: CallbackQuery):
    """Прайс олимпиад после «Узнать прайс»."""
    await callback.answer()

    if not callback.message:
        return

    await callback.message.delete()
    await _send_olympics_course_price_album(callback.message.bot, callback.message.chat.id)


@router.callback_query(F.data == "price_ege_from_buy")
async def callback_price_ege_from_buy(callback: CallbackQuery):
    """ЕГЭ/ОГЭ из ветки «Купить курс» (не с главного); «Назад» — снова выбор направления."""
    await callback.answer()

    if not callback.message:
        return

    await callback.message.delete()
    await _send_ege_course_price_album(
        callback.message.bot,
        callback.message.chat.id,
        course_back_callback="buy_course",
    )


@router.callback_query(F.data == "price_dvi_from_buy")
async def callback_price_dvi_from_buy(callback: CallbackQuery):
    """ДВИ из ветки «Купить курс» (не с главного)."""
    await callback.answer()

    if not callback.message:
        return

    await callback.message.delete()
    await _send_dvi_course_price_album(
        callback.message.bot,
        callback.message.chat.id,
        track_back_callback="buy_course",
    )


@router.callback_query(F.data == "price_olympics_from_buy")
async def callback_price_olympics_from_buy(callback: CallbackQuery):
    """Олимпиады из ветки «Купить курс» (не с главного)."""
    await callback.answer()

    if not callback.message:
        return

    await callback.message.delete()
    await _send_olympics_course_price_album(
        callback.message.bot,
        callback.message.chat.id,
        track_back_callback="buy_course",
    )


@router.callback_query(F.data == "price_ege_from_additional")
async def callback_price_ege_from_additional(callback: CallbackQuery):
    """ЕГЭ/ОГЭ из блока доп. активностей; «Назад» с прайса — снова этот экран."""
    await callback.answer()

    if not callback.message:
        return

    await callback.message.delete()
    await _send_ege_course_price_album(
        callback.message.bot,
        callback.message.chat.id,
        course_back_callback="signup_additional_activities",
    )


@router.callback_query(F.data == "price_olympics_from_additional")
async def callback_price_olympics_from_additional(callback: CallbackQuery):
    """Олимпиады из блока доп. активностей; «Назад» с прайса — снова этот экран."""
    await callback.answer()

    if not callback.message:
        return

    await callback.message.delete()
    await _send_olympics_course_price_album(
        callback.message.bot,
        callback.message.chat.id,
        track_back_callback="signup_additional_activities",
    )


@router.callback_query(F.data == "reviews")
async def callback_reviews(callback: CallbackQuery):
    """Обработчик кнопки 'Посмотреть отзывы' и 'Назад' с карточки отзыва (фото)."""
    await callback.answer()

    if not callback.message:
        return

    bot = callback.message.bot
    chat_id = callback.message.chat.id

    await _delete_review_keyboard_and_photo(callback.message)
    reviews_text = get_reviews_message()
    text_value, entities_value = reviews_text.render()
    await bot.send_message(
        chat_id=chat_id,
        text=text_value,
        entities=entities_value,
        reply_markup=get_reviews_keyboard(),
        parse_mode=None,
    )


@router.callback_query(F.data == "read_reviews")
async def callback_read_reviews(callback: CallbackQuery):
    """Обработчик кнопки 'Читать отзывы' — первый отзыв (фото)."""
    await callback.answer()

    if not callback.message:
        return

    bot = callback.message.bot
    chat_id = callback.message.chat.id

    await _safe_delete_message(callback.message)
    await _send_review_photo_message(bot, chat_id, 1)


@router.callback_query(F.data.startswith("review_"))
async def callback_review(callback: CallbackQuery):
    """Обработчик перехода к следующему отзыву (фото, по кругу)."""
    await callback.answer()

    if not callback.message:
        return

    bot = callback.message.bot
    chat_id = callback.message.chat.id

    try:
        review_id = int(callback.data.split("_")[1])

        if review_id < 1:
            review_id = len(REVIEWS)
        elif review_id > len(REVIEWS):
            review_id = 1

        await _delete_review_keyboard_and_photo(callback.message)
        await _send_review_photo_message(bot, chat_id, review_id)

    except (ValueError, IndexError):
        logger.error("Ошибка при парсинге review_id из callback_data: %s", callback.data)
        await _delete_review_keyboard_and_photo(callback.message)
        await bot.send_message(
            chat_id=chat_id,
            text="Произошла ошибка. Попробуйте выбрать отзыв снова.",
            reply_markup=get_reviews_keyboard(),
            parse_mode="HTML",
        )


EGE_BACK_CALLBACK_FROM_CODE = {code: cb for cb, code in _EGE_BACK_CODES.items()}


def _parse_ege_tariff_callback(callback_data: str) -> tuple[str, str] | None:
    """Возвращает (tariff, course_back_callback) из ege_tariff_{slay|basic}_{code}."""
    parts = callback_data.split("_")
    if len(parts) != 4 or parts[0] != "ege" or parts[1] != "tariff":
        return None
    tariff = parts[2]
    if tariff not in ("slay", "basic"):
        return None
    course_back_callback = EGE_BACK_CALLBACK_FROM_CODE.get(parts[3])
    if not course_back_callback:
        return None
    return tariff, course_back_callback


def _parse_ege_tariff_from_payment(callback_data: str) -> str:
    if callback_data.endswith("_slay"):
        return "slay"
    if callback_data.endswith("_basic"):
        return "basic"
    return "basic"


@router.callback_query(F.data.regexp(r"^ege_tariff_(slay|basic)_[mtahb]$"))
async def callback_ege_tariff_select(callback: CallbackQuery):
    """Выбор тарифа ЕГЭ/ОГЭ — сразу показываем кнопки оплаты без нового сообщения."""
    await callback.answer()

    if not callback.message:
        return

    parsed = _parse_ege_tariff_callback(callback.data)
    if not parsed:
        return

    tariff, course_back_callback = parsed
    await callback.message.edit_reply_markup(
        reply_markup=get_course_info_keyboard(course_back_callback, tariff=tariff),
    )


@router.callback_query(F.data.regexp(r"^ege_tariff_menu_[mtahb]$"))
async def callback_ege_tariff_menu(callback: CallbackQuery):
    """Назад с экрана оплаты — снова выбор тарифа."""
    await callback.answer()

    if not callback.message:
        return

    back_code = callback.data.rsplit("_", 1)[-1]
    course_back_callback = EGE_BACK_CALLBACK_FROM_CODE.get(back_code)
    if not course_back_callback:
        return

    await callback.message.edit_reply_markup(
        reply_markup=get_ege_tariff_keyboard(course_back_callback),
    )


_PAY_CALLBACKS = {
    "pay_2_weeks",
    "pay_2_weeks_slay",
    "pay_2_weeks_basic",
    "pay_1_month",
    "pay_1_month_slay",
    "pay_1_month_basic",
    "pay_dvi_2_weeks",
    "pay_dvi_1_month",
    "pay_olympics_2_weeks",
    "pay_olympics_1_month",
}


# @router.callback_query(F.data.in_(_PAY_CALLBACKS))
# async def callback_pay_tbank(callback: CallbackQuery):
#     """Создаёт платёж в Т‑Банке и выдаёт ссылку на оплату (CRM — только после CONFIRMED)."""
#     await callback.answer()

#     if not callback.message or not callback.data:
#         return

#     user_id = callback.from_user.id

#     try:
#         user = User.get(User.user_id == user_id)
#         application = await create_payment_for_callback(
#             user=user,
#             callback_data=callback.data,
#         )
#         if not application.payment_url:
#             raise TBankError("Нет PaymentURL в ответе банка")

#         payment_text = get_payment_link_message(application.amount)
#         text_value, entities_value = payment_text.render()
#         await callback.message.edit_text(
#             text=text_value,
#             entities=entities_value,
#             reply_markup=get_payment_link_keyboard(application.payment_url),
#             parse_mode=None,
#         )
#     except User.DoesNotExist:
#         logger.error("Пользователь %s не найден в БД", user_id)
#         await callback.message.edit_text(
#             text="Произошла ошибка. Пожалуйста, начните с команды /start",
#             reply_markup=get_payment_confirmation_keyboard(),
#             parse_mode="HTML",
#         )
#     except TBankError as e:
#         logger.error("Ошибка Init Т‑Банка для user=%s: %s", user_id, e)
#         await callback.message.edit_text(
#             text="Не удалось создать ссылку на оплату. Попробуйте позже или напишите менеджеру.",
#             reply_markup=get_payment_confirmation_keyboard(),
#             parse_mode="HTML",
#         )
#     except Exception as e:
#         logger.error("Ошибка при создании оплаты: %s", e, exc_info=True)
#         await callback.message.edit_text(
#             text="Произошла ошибка при создании оплаты. Попробуйте позже.",
#             reply_markup=get_payment_confirmation_keyboard(),
#             parse_mode="HTML",
#         )


@router.callback_query(F.data == "free_materials")
async def callback_free_materials(callback: CallbackQuery):
    """Обработчик кнопки 'Скачать бесплатные материалы'"""
    # Отвечаем на callback, чтобы убрать индикатор загрузки
    await callback.answer()
    
    # Проверяем, что сообщение существует и доступно для редактирования
    if callback.message:
        # Получаем текст и entities
        materials_text = get_free_materials_message()
        text_value, entities_value = materials_text.render()
        
        # Проверяем, есть ли текст в сообщении для редактирования
        if callback.message.text or callback.message.caption:
            # Если есть текст, редактируем сообщение
            try:
                await callback.message.edit_text(
                    text=text_value,
                    entities=entities_value,
                    reply_markup=get_free_materials_keyboard(),
                    parse_mode=None
                )
            except Exception:
                # Если не удалось отредактировать, удаляем и отправляем новое
                await callback.message.delete()
                await callback.message.answer(
                    text=text_value,
                    entities=entities_value,
                    reply_markup=get_free_materials_keyboard(),
                    parse_mode=None
                )
        else:
            # Если нет текста (медиа-группа), удаляем старое сообщение и отправляем новое
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.answer(
                text=text_value,
                entities=entities_value,
                reply_markup=get_free_materials_keyboard(),
                parse_mode=None
            )


@router.callback_query(F.data == "materials_ege")
async def callback_materials_ege(callback: CallbackQuery):
    """Обработчик раздела материалов ЕГЭ"""
    await callback.answer()
    if not callback.message:
        return
    await callback.message.edit_text(
        text="Выбери материал ЕГЭ для скачивания:",
        reply_markup=get_ege_materials_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "materials_olympiad")
async def callback_materials_olympiad(callback: CallbackQuery):
    """Обработчик раздела материалов олимпиад"""
    await callback.answer()
    if not callback.message:
        return
    await callback.message.edit_text(
        text="Выбери материал для олимпиадного направления:",
        reply_markup=get_olympiad_materials_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("download_material_"))
async def callback_download_material(callback: CallbackQuery):
    """Обработчик скачивания материала"""
    # Отвечаем на callback, чтобы убрать индикатор загрузки
    await callback.answer()
    
    if not callback.message:
        return
    
    material_key = callback.data.removeprefix("download_material_")
    material = MATERIALS.get(material_key)
    if not material:
        await callback.message.edit_text(
            text="Материал не найден. Попробуйте выбрать другой.",
            reply_markup=get_free_materials_keyboard(),
            parse_mode="HTML"
        )
        return

    section_callback = material.get("section_callback", "free_materials")
    section_keyboard = (
        get_ege_materials_keyboard()
        if section_callback == "materials_ege"
        else get_olympiad_materials_keyboard()
    )

    try:
        # Проверяем подписку на канал
        if not config.CHANNEL_ID:
            logger.error("CHANNEL_ID не настроен в переменных окружения")
            await callback.message.edit_text(
                text="Произошла ошибка конфигурации. Попробуйте позже.",
                reply_markup=section_keyboard,
                parse_mode="HTML"
            )
            return
        
        try:
            member = await callback.message.bot.get_chat_member(
                chat_id=config.CHANNEL_ID,
                user_id=callback.from_user.id
            )
            is_subscribed = member.status not in ('left', 'kicked')
        except Exception as e:
            logger.error(f"Ошибка при проверке подписки на канал: {e}")
            is_subscribed = False
        
        # Если пользователь не подписан на канал, просим подписаться и возвращаемся к списку материалов
        if not is_subscribed:
            # Получаем текст и entities для сообщения о подписке
            subscription_message = Text(
                "Чтобы скачать бесплатные материалы, ", Bold("нужна подписка на наш канал"),
                " @ladada_eng ",
                CustomEmoji("🎀", custom_emoji_id="5199582550653163382")
            )
            text_value, entities_value = subscription_message.render()
            await callback.message.edit_text(
                text=text_value,
                entities=entities_value,
                reply_markup=section_keyboard,
                parse_mode=None
            )
            return
        
        # Пользователь подписан на канал — отправляем файл
        file_path = material["file_path"]

        # Если файл не существует, возвращаем ошибку в текущий раздел
        if not os.path.exists(file_path):
            logger.error("Файл материала не найден: %s", file_path)
            await callback.message.edit_text(
                text="Файл материала пока недоступен. Попробуйте другой.",
                reply_markup=section_keyboard,
                parse_mode="HTML",
            )
            return
        
        # Отправляем файл напрямую в чат
        try:
            caption = f"<b>{material['title']}</b> 📥"
            
            await media_cache.send_document(
                callback.message.bot,
                callback.message.chat.id,
                file_path,
                filename=os.path.basename(file_path),
                caption=caption,
                parse_mode="HTML",
            )

            success_msg = Text(
                "Материал успешно получен ",
                CustomEmoji("✅", custom_emoji_id="5258265114020181734"),
            )
            success_text, success_entities = success_msg.render()
            await callback.message.bot.send_message(
                chat_id=callback.message.chat.id,
                text=success_text,
                entities=success_entities,
                reply_markup=get_after_download_keyboard("free_materials"),
                parse_mode=None,
            )
            
            logger.info(
                "Пользователь %s скачал материал %s: %s",
                callback.from_user.id,
                material_key,
                material["title"],
            )
            
        except Exception as e:
            logger.error(f"Ошибка при отправке файла: {e}")
            await callback.message.edit_text(
                text="Произошла ошибка при отправке файла. Попробуйте позже.",
                reply_markup=section_keyboard,
                parse_mode="HTML"
            )

    except Exception:
        logger.exception("Ошибка при скачивании материала: %s", callback.data)
        await callback.message.edit_text(
            text="Произошла ошибка. Попробуйте выбрать материал снова.",
            reply_markup=section_keyboard,
            parse_mode="HTML"
        )


@router.callback_query(F.data == "home")
async def callback_home(callback: CallbackQuery):
    """Обработчик кнопки 'Домой' / 'Назад' на главный экран — то же видео, что при /start."""
    await callback.answer()

    if not callback.message:
        return

    bot = callback.message.bot
    chat_id = callback.message.chat.id

    if callback.message.reply_to_message:
        await _delete_review_keyboard_and_photo(callback.message)
    else:
        await _safe_delete_message(callback.message)

    await send_welcome_screen(bot, chat_id)
# ============================================================================
# ВРЕМЕННЫЙ ОБРАБОТЧИК ДЛЯ ИЗВЛЕЧЕНИЯ ID ПРЕМИУМ-ЭМОДЗИ
# Удалите этот обработчик после получения нужных ID
# ============================================================================
@router.message(F.text | F.caption)
async def extract_custom_emoji_ids(message: Message):
    """
    Временный обработчик для извлечения custom_emoji_id из сообщений.
    Отправьте сообщение с премиум-эмодзи, и бот вернет все найденные ID.
    """
    # Проверяем наличие entities в тексте или подписи
    entities = message.entities or message.caption_entities
    
    if not entities:
        return  # Если нет entities, выходим
    
    custom_emoji_ids = []
    
    # Извлекаем все custom_emoji_id из entities
    for entity in entities:
        if entity.type == MessageEntityType.CUSTOM_EMOJI:
            if entity.custom_emoji_id:
                custom_emoji_ids.append(entity.custom_emoji_id)
    
    # Если нашли премиум-эмодзи, получаем информацию о них
    if custom_emoji_ids:
        try:
            # Получаем информацию о стикерах по их ID
            stickers = await message.bot.get_custom_emoji_stickers(
                custom_emoji_ids=custom_emoji_ids
            )
            
            # Формируем ответ с информацией
            result = "🎯 <b>Найденные премиум-эмодзи:</b>\n\n"
            
            for i, sticker in enumerate(stickers, 1):
                result += f"<b>{i}. Эмодзи #{i}</b>\n"
                result += f"   ID: <code>{sticker.custom_emoji_id}</code>\n"
                result += f"   Emoji: {sticker.emoji or 'N/A'}\n"
                result += f"   Набор: {sticker.set_name or 'N/A'}\n"
                result += f"   Анимированный: {'Да' if sticker.is_animated else 'Нет'}\n"
                result += f"   Видео: {'Да' if sticker.is_video else 'Нет'}\n"
                result += f"   Размер: {sticker.width}x{sticker.height}\n\n"
            
            # Добавляем список всех ID для удобного копирования
            result += "📋 <b>Все ID для копирования:</b>\n"
            result += "\n".join([f"<code>{emoji_id}</code>" for emoji_id in custom_emoji_ids])
            
            await message.answer(result, parse_mode="HTML")
            
        except Exception as e:
            logger.error(f"Ошибка при получении информации о стикерах: {e}")
            await message.answer(
                f"❌ Ошибка при получении информации о стикерах:\n<code>{str(e)}</code>",
                parse_mode="HTML"
            )
