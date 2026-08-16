from infrastructure.llm.providers.google_web_search import search_google


# обновленный с гугл поиском
def _clean_source_title(title: str) -> str:
    suffix = " Страница откроется в новой вкладке."

    if title.endswith(suffix):
        title = title[:-len(suffix)]

    return title.strip()


def perform_web_search(
        query: str,
        instructions: str | None = None,
        allowed_domains: list[str] | None = None,
        max_output_tokens: int | None = None,
):
    try:
        result = search_google(query)

        ai_overview = result.get("ai_overview")

        if not ai_overview:
            return (
                "Результаты веб-поиска не содержат AI-обзор.",
                []
            )

        text = (ai_overview.get("text") or "").strip()
        sources = ai_overview.get("sources") or []

        context_parts = []

        if text:
            context_parts.append(
                f"Текст ИИ-обзора веб-поиска:\n{text}"
            )

        if sources:
            source_lines = [
                "Использованные источники:"
            ]

            seen_urls = set()

            for source in sources:
                url = (source.get("url") or "").strip()

                if not url or url in seen_urls:
                    continue

                seen_urls.add(url)

                title = _clean_source_title(
                    source.get("title") or ""
                )

                if title:
                    source_lines.append(
                        f"- {title}: {url}"
                    )
                else:
                    source_lines.append(
                        f"- {url}"
                    )

            if len(source_lines) > 1:
                context_parts.append(
                    "\n".join(source_lines)
                )

        if not context_parts:
            return (
                "Веб-поиск не вернул содержательных результатов.",
                []
            )
        print("Результат веб-поиска:" + "\n\n".join(context_parts) + sources)  # УДАЛИТЬ ПОСЛЕ ОТЛАДКИ
        return "\n\n".join(context_parts), sources

    except Exception:
        return (
            "Веб-поиск временно недоступен. "
            "Используй локальную базу знаний.",
            []
        )

