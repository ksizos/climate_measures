# -*- coding: utf-8 -*-

import os
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ADAPTATION_TABLE = os.getenv("ADAPTATION_TABLE")
NPA_TABLE = os.getenv("NPA_TABLE")
METHOD_DOCS_TABLE = os.getenv("METHOD_DOCS_TABLE")
INTERNET_RESOURCES_TABLE = os.getenv("INTERNET_RESOURCES_TABLE")
FLOOD_OBJECTS_TABLE = os.getenv("FLOOD_OBJECTS_TABLE")

DATA_PATH= Path(os.getenv("DATA_PATH","./data",))
STATISTICS_PATH = Path(os.getenv("STATISTICS_PATH","./data/Statistics_MO",))


LOCAL_LLM_MODEL_NAME = os.getenv(
    "LOCAL_LLM_MODEL_NAME",
    "yandex/YandexGPT-5-Lite-8B-instruct",
)

LOCAL_LLM_CONTEXT_WINDOW = int(
    os.getenv(
        "LOCAL_LLM_CONTEXT_WINDOW",
        "32768",
    )
)

LOCAL_LLM_DEVICE_MAP = os.getenv(
    "LOCAL_LLM_DEVICE_MAP",
    "auto",
)

LOCAL_LLM_TOP_P = float(
    os.getenv(
        "LOCAL_LLM_TOP_P",
        "0.9",
    )
)

ORCHESTRATOR_MAX_TOKENS = int(
    os.getenv(
        "ORCHESTRATOR_MAX_TOKENS",
        "30000",
    )
)

AGGREGATOR_MAX_TOKENS = int(
    os.getenv(
        "AGGREGATOR_MAX_TOKENS",
        "30000",
    )
)


BRIGHT_DATA_API_URL = os.getenv("BRIGHT_DATA_API_URL")
BRIGHT_DATA_TOKEN = os.getenv("BRIGHT_DATA_TOKEN")

EMBED_MODEL = os.getenv("EMBED_MODEL")
EMBED_DIM = int(os.getenv("EMBED_DIM", "1024"))

DB_DATABASE = os.getenv("DB_DATABASE")
DB_HOST = os.getenv("DB_HOST")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USERNAME = os.getenv("DB_USERNAME")

DB_PARAMS = {
    "database": DB_DATABASE,
    "host": DB_HOST,
    "password": DB_PASSWORD,
    "port": DB_PORT,
    "user": DB_USERNAME,
    "embed_dim": EMBED_DIM,
}

PSYCOPG_DB_PARAMS = {
    "database": DB_DATABASE,
    "host": DB_HOST,
    "password": DB_PASSWORD,
    "port": DB_PORT,
    "user": DB_USERNAME,
}

SECTION_TO_INDUSTRY = {
    "Платные услуги населению": "экономика",
    "Розничная торговля и общественное питание": "экономика",
    "Спорт": "социальная сфера",
    "Предприятия по переработке отходов": "коммунальная сфера",
    "Территория": "экономика",
    "Сельское хозяйство": "сельское хозяйство",
    "Коммунальная сфера": "коммунальная сфера",
    "Инвестиции в основной капитал": "экономика",
    "Социальная поддержка по оплате жилых помещений и коммунальных услуг": "социальная сфера",
    "Бухгалтерская отчетность": "экономика",
    "Коллективные средства размещения": "экономика",
    "Почтовая и телефонная связь": "транспорт и дороги",
    "Население": "население",
    "Занятость и заработная плата": "экономика",
    "Здравоохранение": "социальная сфера",
    "Образование": "социальная сфера",
    "Охрана окружающей среды": "коммунальная сфера",
    "Основные фонды организаций (без субъектов малого предпринимательства)": "экономика",
    "Строительство жилья": "экономика",
    "Деятельность предприятий": "экономика",
    "Показатели для оценки эффективности деятельности органов местного самоуправления городских округов и муниципальных районов": "экономика",
    "Финансовая деятельность": "местный бюджет",
    "Сведения о выданных разрешениях и уведомлениях на строительство и на ввод объектов в эксплуатацию": "экономика",
}

PERIOD_PATTERNS = [
    re.compile(r"^январь\-"),
    re.compile(r"^на\s+\d+\s+[а-я]+", re.I),
    re.compile(r"^[IVX]+\s+квартал", re.I),
    re.compile(r"^\d+\s+квартал", re.I),
    re.compile(r"^за\s+\d+\s+месяцев", re.I),
    re.compile(r"^за\s+год$", re.I),
    re.compile(r"^год$", re.I),
    re.compile(r"^на\s+конец\s+года$", re.I),
]

TOP_LEVEL_HINTS = (
    "число ",
    "численность ",
    "количество ",
    "объем ",
    "оборот ",
    "площадь ",
    "оценка ",
    "средн",
    "доля ",
    "обеспеченность ",
    "наличие ",
    "прибыль ",
    "убыток ",
    "сведения ",
    "инвестиции ",
    "ввод ",
    "стоимость ",
    "выпуск ",
    "протяженность ",
    "протяжённость ",
    "мощность ",
    "заболеваемость ",
)

APP_TITLE = os.getenv("APP_TITLE")
