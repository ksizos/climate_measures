from __future__ import annotations

import logging
from dataclasses import dataclass, field

from infrastructure.llm.providers.google_web_search import (
    search_google,
)


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class WebSource:
    """
    Один источник, указанный Google AI Overview.
    """

    source_id: str
    title: str
    url: str


@dataclass(slots=True)
class WebSearchResult:
    """
    Результат Google AI Overview.

    overview:
        текст AI Overview.

    sources:
        references, которые Google указал
        для данного AI Overview.
    """

    query: str
    overview: str = ""

    sources: list[WebSource] = field(
        default_factory=list
    )

    error: str | None = None

    @property
    def found(self) -> bool:
        return bool(
            self.overview
            or self.sources
        )

    def to_context(self) -> str:
        """
        Формирует контекст для локальной YandexGPT.

        В модель передаётся:
        - текст AI Overview;
        - только references этого AI Overview;
        - никаких organic results.
        """

        if not self.found:
            if self.error:
                return (
                    "Google AI Overview временно недоступен."
                )

            return (
                "Google AI Overview не вернул "
                "содержательного результата."
            )

        parts: list[str] = [
            "Контекст Google AI Overview:"
        ]

        if self.overview:
            parts.append(
                "[WEB-OVERVIEW]\n"
                f"{self.overview}"
            )

        if self.sources:
            source_blocks: list[str] = [
                (
                    "Источники, указанные "
                    "в Google AI Overview:"
                )
            ]

            for source in self.sources:
                source_blocks.append(
                    "\n".join(
                        [
                            f"[{source.source_id}]",
                            (
                                "Название: "
                                f"{source.title}"
                            ),
                            f"URL: {source.url}",
                        ]
                    )
                )

            parts.append(
                "\n\n".join(source_blocks)
            )

        return "\n\n---\n\n".join(parts)


def _clean_source_title(
    title: str,
) -> str:
    """
    Убирает технический хвост,
    который иногда приходит из Google.
    """

    suffix = (
        " Страница откроется в новой вкладке."
    )

    title = title.strip()

    if title.endswith(suffix):
        title = title[:-len(suffix)]

    return title.strip()


def perform_web_search(
    query: str,
) -> WebSearchResult:
    """
    Выполняет Google Search через Bright Data
    и возвращает ТОЛЬКО:

    - AI Overview;
    - references AI Overview.

    Organic results здесь не используются.
    """

    clean_query = query.strip()

    if not clean_query:
        return WebSearchResult(
            query="",
            error="Пустой поисковый запрос.",
        )

    logger.info(
        "Google AI Overview search START: %s",
        clean_query[:300],
    )

    try:
        result = search_google(
            clean_query
        )

        ai_overview = (
            result.get("ai_overview")
            or {}
        )

        overview = (
            ai_overview.get("text")
            or ""
        ).strip()

        raw_sources = (
            ai_overview.get("sources")
            or []
        )

        sources: list[WebSource] = []
        seen_urls: set[str] = set()

        for raw_source in raw_sources:
            url = (
                raw_source.get("url")
                or ""
            ).strip()

            if not url:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)

            title = _clean_source_title(
                raw_source.get("title")
                or ""
            )

            if not title:
                title = "Веб-источник"

            sources.append(
                WebSource(
                    source_id=(
                        f"WEB-{len(sources) + 1}"
                    ),
                    title=title,
                    url=url,
                )
            )

        logger.info(
            "Google AI Overview search FINISHED: "
            "overview=%s, sources=%s",
            bool(overview),
            len(sources),
        )

        return WebSearchResult(
            query=clean_query,
            overview=overview,
            sources=sources,
        )

    except Exception as error:
        logger.exception(
            "Ошибка Google AI Overview search"
        )

        return WebSearchResult(
            query=clean_query,
            error=str(error),
        )