from __future__ import annotations

import json

import requests
from urllib.parse import urlencode

from core.config import (
    BRIGHT_DATA_API_URL,
    BRIGHT_DATA_TOKEN,
)


def extract_ai_overview_text(
    node,
) -> list[str]:
    """
    Рекурсивно извлекает текстовые части
    Google AI Overview.
    """

    result: list[str] = []

    if isinstance(node, list):
        for item in node:
            result.extend(
                extract_ai_overview_text(item)
            )

        return result

    if not isinstance(node, dict):
        return result

    node_type = node.get("type")

    if node_type == "paragraph":
        snippet = node.get("snippet")

        if snippet:
            result.append(
                str(snippet).strip()
            )

        return result

    if node_type == "list":
        title = node.get("title")

        if title:
            result.append(
                str(title).strip()
            )

        children = node.get(
            "list",
            [],
        )

        result.extend(
            extract_ai_overview_text(
                children
            )
        )

        return result

    if "list" in node:
        result.extend(
            extract_ai_overview_text(
                node["list"]
            )
        )

    if "snippet" in node:
        snippet = node.get("snippet")

        if snippet:
            result.append(
                str(snippet).strip()
            )
    print(result)
    return result


def get_ai_overview(
    serp: dict,
) -> dict | None:
    """
    Возвращает:

    {
        "text": "...",
        "sources": [
            {
                "title": "...",
                "url": "..."
            }
        ]
    }

    sources — только references,
    указанные самим Google AI Overview.
    """

    ai_overview = serp.get(
        "ai_overview"
    )

    if not ai_overview:
        return None

    text_parts = extract_ai_overview_text(
        ai_overview.get(
            "texts",
            [],
        )
    )

    unique_text_parts: list[str] = []

    for text in text_parts:
        clean_text = text.strip()

        if not clean_text:
            continue

        if clean_text in unique_text_parts:
            continue

        unique_text_parts.append(
            clean_text
        )

    ai_text = "\n\n".join(
        unique_text_parts
    )

    sources: list[dict] = []
    seen_urls: set[str] = set()

    for reference in ai_overview.get(
        "references",
        [],
    ):
        url = (
            reference.get("href")
            or ""
        ).strip()

        if not url:
            continue

        if url in seen_urls:
            continue

        seen_urls.add(url)

        title = (
            reference.get("title")
            or ""
        ).strip()

        sources.append(
            {
                "title": title,
                "url": url,
            }
        )

    return {
        "text": ai_text,
        "sources": sources,
    }


def parse_bright_data_response(
    response: requests.Response,
) -> dict:
    """
    Разбирает Bright Data response.
    """

    response.raise_for_status()

    outer_response = response.json()

    body = outer_response.get("body")

    if body is None:
        raise ValueError(
            "В ответе Bright Data нет 'body'."
        )

    if isinstance(body, str):
        try:
            serp = json.loads(body)

        except json.JSONDecodeError as exc:
            raise ValueError(
                "'body' Bright Data не является JSON."
            ) from exc

    elif isinstance(body, dict):
        serp = body

    else:
        raise ValueError(
            "Неверный тип Bright Data body: "
            f"{type(body).__name__}"
        )

    return {
        "query": (
            serp
            .get("general", {})
            .get("query", "")
        ),

        # Только AI Overview.
        "ai_overview": get_ai_overview(
            serp
        ),
    }


def search_google(
    query: str,
) -> dict:
    """
    Google Search через Bright Data.

    Запрашиваем AI Overview.
    Organic выдача приложением не используется.
    """

    params = {
        "q": query,
        "hl": "ru",
        "gl": "RU",
        "brd_json": "1",
        # Тюмень / Тюменская область.
        "uule": (
            "w CAIQICIUVHl1bWVuIE9ibGFzdCxSdXNzaWE"
        ),

        # Запрашиваем AI Overview.
        "brd_ai_overview": "2",
    }

    google_url = (
        "https://www.google.com/search?"
        + urlencode(params)
    )

    headers = {
        "Authorization": (
            f"Bearer {BRIGHT_DATA_TOKEN}"
        ),
        "Content-Type": "application/json",
    }

    data = {
        "zone": "serp_api1",
        "url": google_url,
        "format": "json",
    }

    response = requests.post(
        BRIGHT_DATA_API_URL,
        json=data,
        headers=headers,
        timeout=60,
    )

    return parse_bright_data_response(
        response
    )