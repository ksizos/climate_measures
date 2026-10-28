from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests
from dotenv import load_dotenv


from core.config import (
    SERPAPI_API_KEY_1,
    SERPAPI_API_KEY_2,
    SERPAPI_SEARCH_URL,
    SERPAPI_ACCOUNT_URL,
    SERPAPI_HL,
    SERPAPI_GL,
    SERPAPI_TIMEOUT,
    SERPAPI_ORGANIC_TOP_K,
)
SERPAPI_LANGUAGE = SERPAPI_HL
SERPAPI_COUNTRY = SERPAPI_GL

logger = logging.getLogger(__name__)


SERPAPI_SEARCH_URL = "https://serpapi.com/search.json"
SERPAPI_ACCOUNT_URL = "https://serpapi.com/account.json"
SERPAPI_TIMEOUT = float(os.getenv("SERPAPI_TIMEOUT", "45"))
SERPAPI_LANGUAGE = os.getenv("SERPAPI_HL", "ru")
SERPAPI_COUNTRY = os.getenv("SERPAPI_GL", "ru")
SERPAPI_ORGANIC_TOP_K = max(1, int(os.getenv("SERPAPI_ORGANIC_TOP_K", "5")))


def _api_keys() -> list[str]:
    keys = [
        SERPAPI_API_KEY_1,
        SERPAPI_API_KEY_2,
    ]

    return list(
        dict.fromkeys(
            key for key in keys if key
        )
    )


@dataclass(slots=True)
class WebSource:
    title: str
    url: str
    snippet: str = ""
    number: int = 0

    @property
    def description(self) -> str:
        return self.snippet


@dataclass(slots=True)
class WebSearchResult:
    query: str = ""
    overview: str = ""
    sources: list[WebSource] = field(default_factory=list)
    error: str | None = None

    def to_context(self) -> str:
        if self.error and not self.overview and not self.sources:
            return f"Внешний поиск временно недоступен: {self.error}"
        if not self.overview and not self.sources:
            return "Релевантные результаты внешнего веб-поиска не найдены."

        parts: list[str] = []
        if self.overview:
            parts.append(
                "=== ВНЕШНЯЯ ПОИСКОВАЯ СВОДКА ===\n"
                "Используй для дополнения ответа. Ссылки на документы и "
                "ресурсы бери только из конкретных источников ниже.\n\n"
                + self.overview
            )
        if self.sources:
            blocks = ["=== КОНКРЕТНЫЕ ВНЕШНИЕ ИСТОЧНИКИ ==="]
            for source in self.sources:
                block = [f"[WEB-{source.number}] {source.title}", f"URL: {source.url}"]
                if source.snippet:
                    block.append(f"Описание: {source.snippet}")
                blocks.append("\n".join(block))
            parts.append("\n\n".join(blocks))
        return "\n\n".join(parts)


class SerpApiError(RuntimeError):
    def __init__(self, reason: str, *, quota_exhausted: bool = False,
                 retry_other_key: bool = False):
        super().__init__(reason)
        self.quota_exhausted = quota_exhausted
        self.retry_other_key = retry_other_key


def _redact(text: str) -> str:
    for api_key in _api_keys():
        text = text.replace(api_key, "[REDACTED]")
    return text


def _get_json(url: str, *, params: dict[str, Any], timeout: float) -> dict[str, Any]:
    try:
        response = requests.get(url, params=params, timeout=timeout)
    except requests.RequestException as exc:
        # requests exceptions may contain the full request URL, including api_key.
        raise SerpApiError(f"Ошибка сети ({type(exc).__name__})") from None

    try:
        data = response.json()
    except ValueError:
        raise SerpApiError(f"Ответ не является JSON (HTTP {response.status_code})") from None

    if not isinstance(data, dict):
        raise SerpApiError("Неожиданный формат JSON")

    message = _redact(str(data.get("error") or "")).strip()
    message_lower = message.lower()
    exhausted = any(phrase in message_lower for phrase in (
        "run out of searches", "no searches left", "out of searches",
        "monthly search limit", "monthly limit", "search credits exhausted",
    ))

    # 429 can also mean hourly throughput, not only monthly exhaustion.
    if response.status_code == 429 and not exhausted:
        raise SerpApiError(
            "Достигнут часовой лимит запросов SerpApi", retry_other_key=True
        )

    if exhausted:
        raise SerpApiError("Месячный лимит ключа исчерпан", quota_exhausted=True,
                           retry_other_key=True)

    if response.status_code in (401, 403):
        raise SerpApiError(
            f"Ключ не авторизован (HTTP {response.status_code})", retry_other_key=True
        )

    if not response.ok:
        raise SerpApiError(f"SerpApi HTTP {response.status_code}: {message[:200]}")

    # A successful search may legitimately contain empty results. Do not rotate
    # keys for that case: changing account won't make Google return an overview.
    if message and "hasn't returned any results" not in message_lower:
        raise SerpApiError(f"SerpApi: {message[:200]}")

    return data


def _account_balance(api_key: str) -> int | None:
    """Exact SerpApi balance. Account API does not consume search credits.

    None means the balance is unknown due to a transient Account API failure.
    """
    try:
        info = _get_json(SERPAPI_ACCOUNT_URL,
                         params={"api_key": api_key}, timeout=10)
        for field_name in ("total_searches_left", "plan_searches_left"):
            value = info.get(field_name)
            if value is not None:
                return max(0, int(value))
    except (SerpApiError, ValueError, TypeError) as exc:
        logger.warning("SerpApi: не удалось проверить остаток одного ключа: %s", exc)
    return None


def get_serpapi_balances() -> list[dict[str, Any]]:
    """For safe diagnostics: never returns the raw keys."""
    return [
        {"key_number": number, "searches_left": _account_balance(key)}
        for number, key in enumerate(_api_keys(), start=1)
    ]


def _key_priority() -> list[tuple[int, str]]:
    keys = _api_keys()
    if not keys:
        return []

    entries = [(index + 1, key, _account_balance(key))
               for index, key in enumerate(keys)]

    # Prefer a key with 2+ credits: a page_token may require a second paid
    # request. Primary first while it has enough; switch to secondary once
    # the primary can't support the full two-stage search.
    with_two = [(number, key) for number, key, left in entries
                if left is None or left >= 2]
    with_one = [(number, key) for number, key, left in entries if left == 1]
    return with_two + with_one


def _normalize_url(value: Any) -> str:
    url = str(value or "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""

    # Google redirect links aren't useful citations. Unwrap only if the
    # redirect explicitly provides a real http(s) target URL.
    host = (parsed.hostname or "").lower()
    if host in {"google.com", "www.google.com"} and parsed.path == "/goto":
        target = parse_qs(parsed.query).get("url", [""])[0]
        target_parsed = urlparse(target)
        if target_parsed.scheme in {"http", "https"} and target_parsed.netloc:
            return target
        return ""
    return url


def _extract_sources(references: list[Any]) -> tuple[list[WebSource], dict[int, int]]:
    """Map original 0-based SerpApi reference indexes to public WEB numbers."""
    sources: list[WebSource] = []
    reference_mapping: dict[int, int] = {}
    url_to_number: dict[str, int] = {}
    for index, item in enumerate(references):
        if not isinstance(item, dict):
            continue
        url = _normalize_url(item.get("link") or item.get("url"))
        if not url:
            continue
        existing = url_to_number.get(url)
        if existing is not None:
            reference_mapping[index] = existing
            continue
        number = len(sources) + 1
        title = str(item.get("title") or item.get("source") or url).strip()
        snippet = str(item.get("snippet") or item.get("description") or "").strip()
        sources.append(WebSource(title=title, url=url, snippet=snippet, number=number))
        url_to_number[url] = number
        reference_mapping[index] = number
    return sources, reference_mapping


def _citations(block: dict[str, Any], reference_mapping: dict[int, int]) -> str:
    result: list[str] = []
    for index in block.get("reference_indexes") or []:
        if isinstance(index, int) and index in reference_mapping:
            number = reference_mapping[index]
            marker = f"[WEB-{number}]"
            if marker not in result:
                result.append(marker)
    return " ".join(result)


def _extract_text(blocks: Any, reference_mapping: dict[int, int], depth: int = 0) -> str:
    if not isinstance(blocks, list) or depth >= 8:
        return ""
    lines: list[str] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        cite = _citations(block, reference_mapping)
        title = str(block.get("title") or "").strip()
        snippet = str(block.get("snippet") or block.get("text") or "").strip()
        if title:
            lines.append(title)
        if snippet:
            lines.append(f"{snippet} {cite}".strip())

        for item in block.get("list") or []:
            if not isinstance(item, dict):
                if isinstance(item, str) and item.strip():
                    lines.append(f"- {item.strip()}")
                continue
            item_title = str(item.get("title") or "").strip()
            item_snippet = str(item.get("snippet") or item.get("text") or "").strip()
            if item_title and item_snippet:
                item_text = f"- {item_title}: {item_snippet}"
            else:
                item_text = f"- {item_title or item_snippet}"
            item_cite = _citations(item, reference_mapping)
            if item_title or item_snippet:
                lines.append(f"{item_text} {item_cite}".strip())
            if item.get("list"):
                nested = _extract_text([{"list": item["list"]}],
                                       reference_mapping, depth + 1)
                if nested:
                    lines.append(nested)
            if item.get("text_blocks"):
                nested = _extract_text(item["text_blocks"],
                                       reference_mapping, depth + 1)
                if nested:
                    lines.append(nested)

        if block.get("text_blocks"):
            nested = _extract_text(block["text_blocks"], reference_mapping, depth + 1)
            if nested:
                lines.append(nested)

        for row in block.get("table") or []:
            if isinstance(row, (list, tuple)):
                lines.append(" | ".join(map(str, row)))
            elif isinstance(row, dict):
                lines.append(" | ".join(map(str, row.values())))

        if cite and not snippet and not block.get("list") and not block.get("text_blocks"):
            lines.append(cite)
    return "\n".join(lines)


def _organic_fallback(google_data: dict[str, Any], query: str) -> WebSearchResult:
    """Use real Google links when AI Overview is unavailable or uncited."""
    sources: list[WebSource] = []
    for item in google_data.get("organic_results") or []:
        if not isinstance(item, dict):
            continue
        url = _normalize_url(item.get("link"))
        if not url or any(existing.url == url for existing in sources):
            continue
        sources.append(WebSource(
            title=str(item.get("title") or url), url=url,
            snippet=str(item.get("snippet") or ""), number=len(sources) + 1,
        ))
        if len(sources) >= SERPAPI_ORGANIC_TOP_K:
            break
    return WebSearchResult(query=query, sources=sources)


def _search_with_key(query: str, *, key_number: int, api_key: str,
                     fallback_keys: list[tuple[int, str]]) -> WebSearchResult:
    google_data = _get_json(
        SERPAPI_SEARCH_URL,
        params={"engine": "google", "q": query, "api_key": api_key,
                "hl": SERPAPI_LANGUAGE, "gl": SERPAPI_COUNTRY},
        timeout=SERPAPI_TIMEOUT,
    )

    overview = google_data.get("ai_overview") or {}
    if not isinstance(overview, dict):
        overview = {}

    # Always fetch page_token immediately: short-lived token, same API key
    # preferred. Do NOT request the follow-up if text_blocks are present.
    page_token = overview.get("page_token")
    if page_token and not overview.get("text_blocks"):
        followup_params = {"engine": "google_ai_overview",
                           "page_token": page_token, "api_key": api_key}
        try:
            followup = _get_json(SERPAPI_SEARCH_URL, params=followup_params,
                                 timeout=SERPAPI_TIMEOUT)
            overview = followup.get("ai_overview") or {}
        except SerpApiError as exc:
            logger.warning("SerpApi: дополнительный AI-запрос с ключом №%s: %s",
                           key_number, exc)
            # On credit exhaustion, another account might still work. A
            # page_token may not be transferable between accounts, though.
            if exc.retry_other_key:
                for other_number, other_key in fallback_keys:
                    if other_key == api_key:
                        continue
                    try:
                        followup_params["api_key"] = other_key
                        followup = _get_json(SERPAPI_SEARCH_URL,
                                             params=followup_params,
                                             timeout=SERPAPI_TIMEOUT)
                        overview = followup.get("ai_overview") or {}
                        break
                    except SerpApiError as other_exc:
                        logger.warning("SerpApi: дополнительный запрос с ключом №%s: %s",
                                       other_number, other_exc)
            # If the secondary fetch fails, use organic results from the
            # original Google response instead of failing the whole search.

    if not isinstance(overview, dict):
        overview = {}
    references = overview.get("references") or []
    if not isinstance(references, list):
        references = []
    sources, mapping = _extract_sources(references)
    overview_text = _extract_text(overview.get("text_blocks") or [], mapping)

    if overview_text.strip() and sources:
        logger.info("SerpApi: ключ №%s, overview и %s источников",
                    key_number, len(sources))
        return WebSearchResult(query=query, overview=overview_text, sources=sources)

    logger.info("SerpApi: ключ №%s, обзор без привязанных URL; используем organic results",
                key_number)
    return _organic_fallback(google_data, query)


def perform_web_search(query: str) -> WebSearchResult:
    """Compatible synchronous API used by NPA/Method/Internet agents.

    Consumers already call it through asyncio.to_thread(), so no agent
    modifications are necessary.
    """
    clean_query = (query or "").strip()
    if not clean_query:
        return WebSearchResult(query="", error="Пустой поисковый запрос")

    candidates = _key_priority()
    if not candidates:
        return WebSearchResult(query=clean_query,
                               error="Не настроены ключи SerpApi или их лимиты исчерпаны")

    last_error: str | None = None
    for number, api_key in candidates:
        try:
            return _search_with_key(clean_query, key_number=number,
                                    api_key=api_key, fallback_keys=candidates)
        except SerpApiError as exc:
            last_error = str(exc)
            logger.warning("SerpApi: ключ №%s: %s", number, last_error)
            if not exc.retry_other_key:
                break

    return WebSearchResult(query=clean_query,
                           error=last_error or "Не удалось получить результаты поиска")


if __name__ == "__main__":
    for item in get_serpapi_balances():
        left = item["searches_left"]
        print(f"Ключ №{item['key_number']}: "
              + (f"осталось {left} запросов" if left is not None else "остаток неизвестен"))
