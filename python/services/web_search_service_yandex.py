from __future__ import annotations

import logging
import re
from urllib.parse import urlparse

from infrastructure.llm.providers.yandex_web_search import (
    WebSearchResult,
    WebSearchSource,
    search_web,
)

logger = logging.getLogger(__name__)

_URL_PATTERN = re.compile(
    r"https?://[^\s)\]}>,]+"
    r"|(?<![\w/])(?:[\w-]+\.)+[a-zA-Z]{2,}"
    r"(?:/[^\s)\]}>,]*)?"
)

def _normalize_domain(
    value: str,
) -> str:
    return (
        value.strip()
        .lower()
        .removeprefix("https://")
        .removeprefix("http://")
        .rstrip("/")
    )


def _domain_matches(
    url: str,
    allowed_domains: list[str],
) -> bool:
    host = (
        urlparse(url).hostname
        or ""
    ).lower()

    for domain in allowed_domains:
        normalized_domain = _normalize_domain(
            domain
        )

        if (
            host == normalized_domain
            or host.endswith(
                "." + normalized_domain
            )
        ):
            return True

    return False


def _remove_urls(
    text: str,
) -> str:
    """
    Убирает URL из контекста для NVIDIA.
    """

    return _URL_PATTERN.sub(
        "[ссылка добавляется программно]",
        text,
    )


def _deduplicate_sources(
    sources: list[WebSearchSource],
) -> list[WebSearchSource]:
    result: list[WebSearchSource] = []
    seen_urls: set[str] = set()

    for source in sources:
        normalized_url = (
            source.url.strip().rstrip("/")
        )

        if not normalized_url:
            continue

        if normalized_url in seen_urls:
            continue

        seen_urls.add(normalized_url)

        result.append(
            WebSearchSource(
                url=normalized_url,
                title=source.title.strip(),
            )
        )

    return result


def perform_web_search(
    query: str,
    *,
    instructions: str | None = None,
    allowed_domains: list[str] | None = None,
    max_output_tokens: int = 2200,
) -> WebSearchResult:
    """
    Выполняет внешний поиск через Yandex.

    При ошибке возвращает безопасный пустой результат,
    чтобы агент мог продолжить работу с PGVector.
    """

    try:
        result = search_web(
            query=query,
            instructions=instructions,
            allowed_domains=allowed_domains,
            temperature=0.1,
            max_output_tokens=max_output_tokens,
        )

        sources = _deduplicate_sources(
            result.sources
        )

        if allowed_domains:
            filtered_sources = [
                source
                for source in sources
                if _domain_matches(
                    source.url,
                    allowed_domains,
                )
            ]

            # Используем отфильтрованные источники,
            # даже если список оказался пустым.
            # Это не позволит неофициальным источникам
            # пройти в ответ при строгом allowlist.
            sources = filtered_sources

        logger.info(
            "Web Search завершён: "
            "query=%s, used=%s, sources=%s",
            query[:200],
            result.used_web_search,
            len(sources),
        )

        return WebSearchResult(
            query=result.query,
            text=result.text,
            sources=sources,
            used_web_search=result.used_web_search,
            response_id=result.response_id,
            raw_response=result.raw_response,
        )

    except Exception:
        logger.exception(
            "Ошибка внешнего Web Search"
        )

        return WebSearchResult(
            query=query,
            text=(
                "Внешний веб-поиск временно "
                "недоступен. Используй локальную "
                "векторную базу. Не делай вывод, "
                "что документы или ресурсы отсутствуют."
            ),
            sources=[],
            used_web_search=False,
            response_id=None,
            raw_response=None,
        )


def build_web_facts_context(
    result: WebSearchResult,
) -> str:
    """
    Формирует фактический контекст без URL.
    """

    clean_text = _remove_urls(
        result.text.strip()
    )

    parts = [
        "Результат внешнего веб-поиска:",
        clean_text,
    ]

    if result.sources:
        source_markers = []

        for index, source in enumerate(
            result.sources,
            start=1,
        ):
            title = (
                source.title
                or "Внешний источник"
            )

            source_markers.append(
                f"[WEB-{index}] {title}"
            )

        parts.extend(
            [
                "",
                "Идентификаторы веб-источников:",
                "\n".join(source_markers),
            ]
        )

    return "\n".join(parts).strip()


def append_exact_web_sources(
    answer: str,
    result: WebSearchResult,
) -> str:
    """
    Добавляет точные URL после генерации NVIDIA.
    """

    if not result.sources:
        return answer.strip()

    lines = [
        answer.strip(),
        "",
        "### Источники веб-поиска",
    ]

    for index, source in enumerate(
        result.sources,
        start=1,
    ):
        title = (
            source.title
            or f"Веб-источник {index}"
        )

        lines.append(
            f"{index}. {title}\n"
            f"   {source.url}"
        )

    return "\n".join(lines)
