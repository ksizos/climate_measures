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

LLM_ORCHESTRATOR_PROVIDER = os.getenv("LLM_ORCHESTRATOR_PROVIDER","nvidia",).strip().lower()
LLM_SPECIALIZED_AGENT_PROVIDER = os.getenv("LLM_SPECIALIZED_AGENT_PROVIDER","nvidia",).strip().lower()
LLM_ADAPTATION_PROVIDER = os.getenv("LLM_ADAPTATION_PROVIDER","nvidia",).strip().lower()
LLM_DIALOG_PROVIDER = os.getenv("LLM_DIALOG_PROVIDER","nvidia",).strip().lower()
LLM_NPA_PROVIDER = os.getenv("LLM_NPA_PROVIDER","nvidia",).strip().lower()
LLM_METHOD_DOCS_PROVIDER = os.getenv("LLM_METHOD_DOCS_PROVIDER","nvidia",).strip().lower()
LLM_INTERNET_RESOURCES_PROVIDER = os.getenv("LLM_INTERNET_RESOURCES_PROVIDER","nvidia",).strip().lower()
LLM_STATISTICS_SQL_PROVIDER = os.getenv("LLM_STATISTICS_SQL_PROVIDER","nvidia",).strip().lower()
LLM_STATISTICS_ANSWER_PROVIDER = os.getenv("LLM_STATISTICS_ANSWER_PROVIDER","nvidia",).strip().lower()
LLM_STRUCTURED_DATA_PROVIDER = os.getenv("LLM_STRUCTURED_DATA_PROVIDER","nvidia",).strip().lower()

LLM_ORCHESTRATOR_MODEL = os.getenv("LLM_ORCHESTRATOR_MODEL")
LLM_SPECIALIZED_AGENT_MODEL = os.getenv("LLM_SPECIALIZED_AGENT_MODEL")
LLM_DIALOG_MODEL = os.getenv("LLM_DIALOG_MODEL")
LLM_ADAPTATION_MODEL = os.getenv("LLM_ADAPTATION_MODEL")
LLM_NPA_MODEL = os.getenv("LLM_NPA_MODEL")
LLM_METHOD_DOCS_MODEL = os.getenv("LLM_METHOD_DOCS_MODEL")
LLM_INTERNET_RESOURCES_MODEL = os.getenv("LLM_INTERNET_RESOURCES_MODEL")
LLM_STATISTICS_SQL_MODEL = os.getenv("LLM_STATISTICS_SQL_MODEL")
LLM_STATISTICS_ANSWER_MODEL = os.getenv("LLM_STATISTICS_ANSWER_MODEL")
LLM_STRUCTURED_DATA_MODEL = os.getenv("LLM_STRUCTURED_DATA_MODEL")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL")
OPENROUTER_REQUEST_TIMEOUT = float(os.getenv("OPENROUTER_REQUEST_TIMEOUT","180",))
OPENROUTER_MAX_RETRIES = int(os.getenv("OPENROUTER_MAX_RETRIES","1",))

ORCHESTRATOR_TEMPERATURE = float(os.getenv("ORCHESTRATOR_TEMPERATURE","0.1"))
ORCHESTRATOR_MAX_TOKENS = int(os.getenv("ORCHESTRATOR_MAX_TOKENS","1500"))
AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE","0.1"))
AGENT_MAX_TOKENS = int(os.getenv("AGENT_MAX_TOKENS","1500"))

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL")
NVIDIA_REQUEST_TIMEOUT = float( os.getenv("NVIDIA_REQUEST_TIMEOUT", "240"))
NVIDIA_MAX_RETRIES = int(os.getenv("NVIDIA_MAX_RETRIES", "0"))

YANDEX_CLOUD_API_KEY = os.getenv("YANDEX_CLOUD_API_KEY")
YANDEX_CLOUD_BASE_URL = os.getenv(
    "YANDEX_CLOUD_BASE_URL",
    "https://rest-assistant.api.cloud.yandex.net/v1",
)
YANDEX_CLOUD_FOLDER = os.getenv("YANDEX_CLOUD_FOLDER")
YANDEX_CLOUD_MODEL = os.getenv(
    "YANDEX_CLOUD_MODEL",
    "yandexgpt",
)
YANDEX_WEB_SEARCH_ENABLED = (
    os.getenv(
        "YANDEX_WEB_SEARCH_ENABLED",
        "true",
    ).strip().lower()
    in {
        "1",
        "true",
        "yes",
        "on",
    }
)
YANDEX_WEB_SEARCH_TIMEOUT = float(
    os.getenv(
        "YANDEX_WEB_SEARCH_TIMEOUT",
        "180",
    )
)
YANDEX_WEB_SEARCH_MAX_RESULTS = int(os.getenv("YANDEX_WEB_SEARCH_MAX_RESULTS","8",))
YANDEX_WEB_SEARCH_MAX_OUTPUT_TOKENS = int(os.getenv("YANDEX_WEB_SEARCH_MAX_OUTPUT_TOKENS","2500",))

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
