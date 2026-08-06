from __future__ import annotations

import logging
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from openai import OpenAI

from core.config import (
    YANDEX_CLOUD_API_KEY,
    YANDEX_CLOUD_BASE_URL,
    YANDEX_CLOUD_FOLDER,
    YANDEX_CLOUD_MODEL,
    YANDEX_WEB_SEARCH_ENABLED,
    YANDEX_WEB_SEARCH_MAX_OUTPUT_TOKENS,
    YANDEX_WEB_SEARCH_TIMEOUT,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class WebSearchSource:
    """
    Один источник, обнаруженный в ответе Yandex.
    """

    url: str
    title: str = ""


@dataclass(slots=True)
class WebSearchResult:
    """
    Унифицированный результат внешнего поиска.
    """

    query: str
    text: str

    sources: list[WebSearchSource] = field(
        default_factory=list,
    )

    used_web_search: bool = False

    response_id: str | None = None

    raw_response: Any | None = None

    @property
    def sources_text(self) -> str:
        """
        Форматирует источники для передачи в NVIDIA.
        """

        if not self.sources:
            return ""

        lines: list[str] = []

        for index, source in enumerate(
            self.sources,
            start=1,
        ):
            if source.title:
                lines.append(
                    f"{index}. {source.title}: "
                    f"{source.url}"
                )
            else:
                lines.append(
                    f"{index}. {source.url}"
                )

        return "\n".join(lines)

    def to_context(self) -> str:
        """
        Формирует готовый контекст для LLM.
        """

        parts = [
            "Результат внешнего веб-поиска:",
            self.text.strip(),
        ]

        sources_text = self.sources_text

        if sources_text:
            parts.extend(
                [
                    "",
                    "Источники веб-поиска:",
                    sources_text,
                ]
            )

        return "\n".join(parts).strip()


def _validate_configuration() -> None:
    if not YANDEX_WEB_SEARCH_ENABLED:
        raise RuntimeError(
            "Yandex Web Search отключён через "
            "YANDEX_WEB_SEARCH_ENABLED."
        )

    if not YANDEX_CLOUD_API_KEY:
        raise RuntimeError(
            "Не задан YANDEX_CLOUD_API_KEY."
        )

    if not YANDEX_CLOUD_FOLDER:
        raise RuntimeError(
            "Не задан YANDEX_CLOUD_FOLDER."
        )

    if not YANDEX_CLOUD_BASE_URL:
        raise RuntimeError(
            "Не задан YANDEX_CLOUD_BASE_URL."
        )

    if not YANDEX_CLOUD_MODEL:
        raise RuntimeError(
            "Не задан YANDEX_CLOUD_MODEL."
        )


def _build_model_uri() -> str:
    """
    Позволяет указывать в env как короткое имя модели,
    так и полный gpt:// URI.
    """

    model = YANDEX_CLOUD_MODEL.strip()

    if model.startswith("gpt://"):
        return model

    return (
        f"gpt://{YANDEX_CLOUD_FOLDER}/"
        f"{model}"
    )


@lru_cache(maxsize=1)
def _get_client() -> OpenAI:
    _validate_configuration()

    return OpenAI(
        api_key=YANDEX_CLOUD_API_KEY,
        project=YANDEX_CLOUD_FOLDER,
        base_url=(
            YANDEX_CLOUD_BASE_URL
            .strip()
            .rstrip("/")
        ),
        timeout=YANDEX_WEB_SEARCH_TIMEOUT,

        # Контролируем ошибки на уровне сервиса.
        max_retries=0,
    )


def _collect_sources(
    value: Any,
    result: dict[str, WebSearchSource],
) -> None:
    """
    Рекурсивно ищет URL и названия источников
    в model_dump() ответа.

    Формат Responses API может содержать ссылки
    в annotations, citations и других вложенных полях.
    """

    if isinstance(value, dict):
        url = value.get("url")

        if isinstance(url, str):
            clean_url = _normalize_url(url)

            if clean_url.startswith(
                ("http://", "https://")
            ):
                title = (
                    value.get("title")
                    or value.get("name")
                    or ""
                )

                result.setdefault(
                    clean_url,
                    WebSearchSource(
                        url=clean_url,
                        title=str(title).strip(),
                    ),
                )

        for child in value.values():
            _collect_sources(
                child,
                result,
            )

    elif isinstance(value, list):
        for child in value:
            _collect_sources(
                child,
                result,
            )


def _extract_sources(
    response_dump: dict[str, Any],
) -> list[WebSearchSource]:
    sources_by_url: dict[
        str,
        WebSearchSource,
    ] = {}

    _collect_sources(
        response_dump,
        sources_by_url,
    )

    return list(
        sources_by_url.values()
    )


def _detect_web_search_usage(
    response_dump: dict[str, Any],
) -> bool:
    """
    Рекурсивно ищет признаки реального вызова web search.
    """

    markers = {
        "web_search",
        "web_search_call",
        "web_search_2025_08_26",
    }

    def contains_web_search(value: Any) -> bool:
        if isinstance(value, str):
            normalized = value.strip().lower()
            return normalized in markers

        if isinstance(value, dict):
            for key, child in value.items():
                key_normalized = str(key).lower()

                if (
                    "web_search" in key_normalized
                    and child not in (None, False, "", [])
                ):
                    return True

                if contains_web_search(child):
                    return True

        elif isinstance(value, list):
            return any(
                contains_web_search(item)
                for item in value
            )

        return False

    return contains_web_search(
        response_dump.get("output", [])
    )

def _normalize_url(value: str) -> str:
    url = value.strip()

    if not url:
        return ""

    if url.startswith(("http://", "https://")):
        return url

    if "." in url and " " not in url:
        return f"https://{url}"

    return ""

def _build_web_search_tool(
    allowed_domains: list[str] | None,
) -> dict[str, Any]:
    """
    Создаёт конфигурацию hosted tool web_search.

    Домены нормализуются без протокола и завершающего /.
    """

    tool: dict[str, Any] = {
        "type": "web_search",
    }

    if not allowed_domains:
        return tool

    normalized_domains = []

    for domain in allowed_domains:
        clean_domain = (
            domain.strip()
            .removeprefix("https://")
            .removeprefix("http://")
            .rstrip("/")
        )

        if clean_domain:
            normalized_domains.append(
                clean_domain
            )

    if normalized_domains:
        tool["filters"] = {
            "allowed_domains": (
                normalized_domains
            )
        }

    return tool

def search_web(
    query: str,
    *,
    instructions: str | None = None,
    allowed_domains: list[str] | None = None,
    temperature: float = 0.1,
    max_output_tokens: int | None = None,
) -> WebSearchResult:
    """
    Выполняет настоящий поиск в интернете через
    встроенный инструмент web_search Yandex AI Studio.

    Функция не формирует итоговый ответ приложения.
    Она возвращает поисковую выжимку и источники,
    которые затем передаются модели NVIDIA.
    """

    clean_query = query.strip()

    if not clean_query:
        raise ValueError(
            "Поисковый запрос не может быть пустым."
        )

    client = _get_client()

    final_instructions = instructions or (
        "Обязательно используй встроенный инструмент web_search. "
        "Не пиши названия инструментов, служебные маркеры, "
        "TOOL_CALL_START или псевдовызовы. "
        "После завершения поиска верни краткую фактическую выжимку. "
        "Для каждого найденного документа укажи название, номер, дату, "
        "орган власти и прямую ссылку. "
        "Не придумывай ссылки и документы."
    )

    tool = _build_web_search_tool(
        allowed_domains=allowed_domains,
    )

    selected_max_tokens = (
        max_output_tokens
        if max_output_tokens is not None
        else YANDEX_WEB_SEARCH_MAX_OUTPUT_TOKENS
    )

    logger.info(
        "Yandex Web Search START: "
        "model=%s query=%s",
        _build_model_uri(),
        clean_query[:300],
    )

    response = client.responses.create(
    model=_build_model_uri(),
    instructions=final_instructions,
    input=clean_query,
    tools=[tool],
    temperature=temperature,
    max_output_tokens=selected_max_tokens,
    )

    response_dump = response.model_dump()

    text = (
        getattr(
            response,
            "output_text",
            None,
        )
        or ""
    ).strip()

    if not text:
        raise RuntimeError(
            "Yandex Web Search не вернул "
            "текстовый результат."
        )

    sources = _extract_sources(
        response_dump
    )

    used_web_search = (
        _detect_web_search_usage(
            response_dump
        )
    )

    if not used_web_search:
        raise RuntimeError(
        "Yandex вернул текстовый ответ, "
        "но реальный инструмент web_search "
        "не был вызван."
    )

    logger.info(
        "Yandex Web Search FINISHED: "
        "used=%s sources=%s response_id=%s",
        used_web_search,
        len(sources),
        getattr(response, "id", None),
    )

    return WebSearchResult(
        query=clean_query,
        text=text,
        sources=sources,
        used_web_search=used_web_search,
        response_id=getattr(
            response,
            "id",
            None,
        ),
        raw_response=response,
    )
