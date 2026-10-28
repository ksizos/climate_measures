
"""Формирование ссылок на поиск научных статей в TrendCarbon.

LLM извлекает поисковую фразу; поиск на самом сайте не выполняется.
"""
from __future__ import annotations

import json
import logging
import re
from urllib.parse import urlencode

from infrastructure.llm.provider import achat_text

logger = logging.getLogger(__name__)

TRENDCARBON_ARTICLES_URL = "https://trend-carbon.utmn.ru/articles"
MAX_QUERY_LENGTH = 180

SEARCH_QUERY_SYSTEM_PROMPT = """
Ты — модуль подготовки поисковых запросов для каталога научных статей.
Твоя задача — извлечь из сообщения пользователя ОДНУ поисковую фразу,
которая будет вставлена в параметр query URL поиска.

Правила:
1. Если пользователь ищет статьи по теме — выдели предметную тему или ключевые слова.
   Убери фразы «найди научные статьи», «подбери публикации», «мне нужны работы».
2. Если указан автор — сохрани его фамилию/имя/инициалы без выдумывания данных.
3. Если указано точное название статьи — сохрани его максимально точно.
4. Учитывай историю диалога только для разрешения ссылок «по этой теме»,
   «этого автора» и подобных; при нехватке данных ничего не додумывай.
5. Не придумывай названия статей, авторов, годы, даты или другие ограничения.
6. Предпочитай короткую информативную фразу; обычно 2–8 слов.
   Исключение — точное название статьи или имя автора.
7. Не добавляй URL, кавычки вокруг всей фразы и URL-кодирование.
8. Если пользователь не указал ни тему, ни автора, ни название статьи,
   верни пустую строку.
9. Верни ТОЛЬКО корректный JSON без Markdown по формату:
   {"query": "поисковые слова"}
""".strip()


def _clean_query(value: str) -> str:
    """Нормализует пробелы и удаляет служебные символы из фразы."""
    value = re.sub(r"[\x00-\x1f\x7f]", " ", value)
    value = " ".join(value.split())
    return value.strip(" \t\n\"'«».,;:!?")[:MAX_QUERY_LENGTH].strip()


def _parse_llm_query(response: str) -> str | None:
    """Читает поле query даже при случайном обрамлении ответа Markdown."""
    raw = (response or "").strip()
    start = raw.find("{")
    if start == -1:
        return None

    try:
        payload, _ = json.JSONDecoder().raw_decode(raw[start:])
    except (ValueError, TypeError):
        return None

    if not isinstance(payload, dict) or not isinstance(payload.get("query"), str):
        return None

    # Пустая строка — валидный ответ, если критерии поиска не заданы.
    return _clean_query(payload["query"])


def _fallback_query(user_question: str) -> str:
    """Простой резервный способ извлечения фразы при ошибке LLM."""
    question = " ".join((user_question or "").split()).strip()
    if not question:
        return ""

    quoted = re.search(r'[«"“]([^»"”]{2,180})[»"”]', question)
    if quoted:
        return _clean_query(quoted.group(1))

    patterns = (
        r"\b(?:по\s+теме|на\s+тему|по\s+автору|автора|авторов|"
        r"по\s+названию|по\s+ключевым\s+словам)\s*[:–-]?\s*(.+)$",
        r"\b(?:об|о|про)\s+(.+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, question, flags=re.IGNORECASE)
        if match:
            return _clean_query(match.group(1))

    remainder = re.sub(
        r"^(?:найди|найдите|подбери|подберите|покажи|покажите|"
        r"поищи|ищу|нужны|хочу\s+найти|мне\s+нужны)\s+",
        "",
        question,
        flags=re.IGNORECASE,
    )
    remainder = re.sub(
        r"^(?:(?:научные|научных|рецензируемые|рецензируемых)\s+)?"
        r"(?:статьи|статей|публикации|публикаций|работы|работ|исследования|"
        r"исследований)\b(?:\s+(?:по|про|о|об))?\s*",
        "",
        remainder,
        flags=re.IGNORECASE,
    )
    if remainder == question or not remainder:
        return ""
    return _clean_query(remainder)


async def extract_article_query_with_llm(
    user_question: str,
    conversation_history: str | None = None,
) -> str:
    """Запрашивает оптимальную поисковую фразу у существующей LLM."""
    user_question = (user_question or "").strip()
    if not user_question:
        return ""

    history = (conversation_history or "")[-1500:]
    llm_prompt = (
        f"История диалога (если есть):\n{history or 'Нет'}\n\n"
        f"Текущий запрос пользователя:\n{user_question}\n\n"
        "Составь JSON с одним полем query."
    )

    try:
        response = await achat_text(
            system_prompt=SEARCH_QUERY_SYSTEM_PROMPT,
            user_prompt=llm_prompt,
            temperature=0.0,
            max_new_tokens=128,
        )
        query = _parse_llm_query(response)
        if query is not None:
            logger.info("TrendCarbon: запрос подготовлен LLM: %s", query)
            return query
        logger.warning("TrendCarbon: LLM вернула ответ без валидного поля query")
    except Exception:
        logger.exception("TrendCarbon: не удалось получить поисковую фразу от LLM")

    return _fallback_query(user_question)


def build_trendcarbon_url(query: str) -> str:
    """Строит URL с фиксированным адресом и безопасным кодированием query."""
    query = _clean_query(query or "")
    if not query:
        return TRENDCARBON_ARTICLES_URL

    return f"{TRENDCARBON_ARTICLES_URL}?{urlencode({'query': query, 'page': 1})}"


async def generate_scientific_articles_response(
    user_question: str,
    conversation_history: str | None = None,
) -> str:
    """Публичный интерфейс агента; совместим с agents/registry.py."""
    query = await extract_article_query_with_llm(
        user_question=user_question,
        conversation_history=conversation_history,
    )
    url = build_trendcarbon_url(query)

    if not query:
        return (
            "Для поиска научных статей используйте аналитическую платформу **TrendCarbon**: https://trend-carbon.utmn.ru/.\n\n"
        )

    return (
        "Для поиска научных статей используйте аналитическую платформу **TrendCarbon**: https://trend-carbon.utmn.ru/.\n\n"
        f"Посмотреть результаты поиска на тему **{query}** в TrendCarbon: [ссылка]({url})\n\n"
    )
