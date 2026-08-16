import json
import requests
from urllib.parse import urlencode

from core.config import (
    BRIGHT_DATA_API_URL,
    BRIGHT_DATA_TOKEN
)


def extract_ai_overview_text(node):
    result = []

    if isinstance(node, list):

        for item in node:
            result.extend(extract_ai_overview_text(item))

        return result

    if not isinstance(node, dict):
        return result

    node_type = node.get("type")

    if node_type == "paragraph":

        snippet = node.get("snippet")

        if snippet:
            result.append(snippet.strip())

        return result

    if node_type == "list":

        title = node.get("title")

        if title:
            result.append(title.strip())

        children = node.get("list", [])

        result.extend(
            extract_ai_overview_text(children)
        )

        return result

    if "list" in node:
        result.extend(
            extract_ai_overview_text(node["list"])
        )

    if "snippet" in node:
        snippet = node.get("snippet")

        if snippet:
            result.append(snippet.strip())

    return result


def get_ai_overview(serp):
    ai_overview = serp.get("ai_overview")

    if not ai_overview:
        return None

    text_parts = extract_ai_overview_text(
        ai_overview.get("texts", [])
    )
    text_parts = [
        text.strip()
        for text in text_parts
        if text and text.strip()
    ]

    unique_text_parts = []

    for text in text_parts:

        if text not in unique_text_parts:
            unique_text_parts.append(text)

    ai_text = "\n\n".join(unique_text_parts)

    sources = []

    for reference in ai_overview.get("references", []):

        url = reference.get("href")
        title = reference.get("title")

        if not url:
            continue

        source = {
            "title": title or "",
            "url": url
        }

        sources.append(source)

    return {
        "text": ai_text,
        "sources": sources
    }


"""
def get_organic_results(serp):
    results = []

    for item in serp.get("organic", []):

        result = {
            "link": item.get("link", ""),
            "source": item.get("source", ""),
            "title": item.get("title", ""),
            "description": item.get("description", "")
        }

        if not any(result.values()):
            continue

        results.append(result)

    return results
"""


def parse_bright_data_response(response):
    response.raise_for_status()

    outer_response = response.json()

    body = outer_response.get("body")

    if body is None:
        raise ValueError(
            "В ответе нет 'body'"
        )

    if isinstance(body, str):

        try:
            serp = json.loads(body)

        except json.JSONDecodeError as exc:
            raise ValueError(
                "'body' не JSON"
            ) from exc

    elif isinstance(body, dict):

        serp = body

    else:

        raise ValueError(
            f"Неверный тип 'body': "
            f"{type(body).__name__}"
        )

    result = {
        "query": serp.get("general", {}).get("query", ""),
        "ai_overview": get_ai_overview(serp)
        # "organic_results": get_organic_results(serp) - если нужна выдача
    }

    return result


# ключевая функция
def search_google(query):
    params = {
        "q": query,
        "hl": "ru",
        "gl": "RU",
        "uule": "w CAIQICIUVHl1bWVuIE9ibGFzdCxSdXNzaWE",
        "brd_ai_overview": "2"
    }

    google_url = (
            "https://www.google.com/search?"
            + urlencode(params)
    )

    headers = {
        "Authorization": f"Bearer {BRIGHT_DATA_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "zone": "serp_api1",
        "url": google_url,
        "format": "json",
        "data_format": "parsed"
    }

    response = requests.post(
        BRIGHT_DATA_API_URL,
        json=data,
        headers=headers,
        timeout=60
    )

    result = parse_bright_data_response(response)

    return result
