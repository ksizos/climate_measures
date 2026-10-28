
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from core.config import ANALYTICAL_DOCS_TABLE, ANALYTICAL_WEB_SEARCH
from infrastructure.llm.provider import achat_text
from prompts.analytical import ANALYTICAL_SYSTEM_PROMPT
from services.vector_context_service import (
    RetrievedVectorDocument,
    retrieve_vector_context,
)
from services.web_search_service import perform_web_search

logger = logging.getLogger(__name__)

ANALYTICAL_CATALOG_TOP_K = 3
ANALYTICAL_CONTENT_TOP_K_PER_DOCUMENT = 2


@dataclass(slots=True)
class AnalyticalLocalContextResult:
    catalog_documents: list[RetrievedVectorDocument] = field(default_factory=list)
    content_documents: dict[str, list[RetrievedVectorDocument]] = field(default_factory=dict)

    @property
    def content_count(self) -> int:
        return sum(len(chunks) for chunks in self.content_documents.values())

    def to_context(self) -> str:
        if not self.catalog_documents:
            return "В локальной базе релевантные аналитические документы не найдены."

        parts = ["=== КАРТОЧКИ ЛОКАЛЬНЫХ АНАЛИТИЧЕСКИХ ДОКУМЕНТОВ ==="]
        for index, doc in enumerate(self.catalog_documents, start=1):
            meta = doc.metadata or {}
            analytical_id = str(meta.get("analytical_id", ""))
            title = str(meta.get("title", ""))
            form = str(meta.get("form", ""))
            description = str(meta.get("description", ""))
            url = str(meta.get("url", ""))

            card = [
                f"[ANALYTICAL-DOC-{index}]",
                f"Форма: {form}",
                f"Название: {title}",
                f"Краткое описание: {description}",
                f"URL: {url}",
            ]
            parts.append("\n".join(card))

            chunks = self.content_documents.get(analytical_id, [])
            if not chunks:
                parts.append("Полный текст этого документа не найден в поисковом контексте.")
                continue

            for chunk_number, chunk in enumerate(chunks, start=1):
                page = (chunk.metadata or {}).get("page_label", "")
                parts.append("\n".join([
                    f"[ANALYTICAL-DOC-{index}-CONTENT-{chunk_number}]",
                    f"Документ: {title}",
                    f"Страница: {page}",
                    f"Фрагмент полного текста:\n{chunk.text}",
                ]))

        return "\n\n---\n\n".join(parts)


def retrieve_analytical_local_context(query: str) -> AnalyticalLocalContextResult:
    """Два этапа поиска в одной таблице: catalog TOP-3 → content TOP-2 на документ."""
    catalog = retrieve_vector_context(
        query,
        table_name=ANALYTICAL_DOCS_TABLE,
        top_k=ANALYTICAL_CATALOG_TOP_K,
        metadata_filters={"record_type": "catalog"},
    )
    result = AnalyticalLocalContextResult(catalog_documents=catalog.documents)

    for card in catalog.documents:
        analytical_id = str((card.metadata or {}).get("analytical_id", "")).strip()
        if not analytical_id:
            logger.warning("Analytical catalog node without analytical_id")
            continue
        content = retrieve_vector_context(
            query,
            table_name=ANALYTICAL_DOCS_TABLE,
            top_k=ANALYTICAL_CONTENT_TOP_K_PER_DOCUMENT,
            metadata_filters={"record_type": "content", "analytical_id": analytical_id},
        )
        result.content_documents[analytical_id] = content.documents

    logger.info(
        "Analytical retrieval: documents=%d chunks=%d",
        len(result.catalog_documents), result.content_count,
    )
    return result


async def generate_analytical_response(
    user_question: str,
    conversation_history: str | None = None,
) -> str:
    logger.info("Analytical service START: %s", user_question)

    local_task = asyncio.to_thread(retrieve_analytical_local_context, user_question)
    web_context = "Внешний веб-поиск отключён настройкой приложения."

    if ANALYTICAL_WEB_SEARCH:
        web_query = (
            "аналитические научные доклады исследования климатические риски "
            "изменение климата устойчивое развитие адаптация "
            f"{user_question}"
        )
        local_result, web_result = await asyncio.gather(
            local_task,
            asyncio.to_thread(perform_web_search, web_query),
        )
        web_context = web_result.to_context()
    else:
        local_result = await local_task

    history = f"История диалога:\n{conversation_history}\n\n" if conversation_history else ""
    user_prompt = f"""
{history}Вопрос пользователя:
{user_question}

=== ЛОКАЛЬНАЯ БАЗА АНАЛИТИЧЕСКИХ ДОКУМЕНТОВ ===
{local_result.to_context()}

=== ДОПОЛНИТЕЛЬНЫЙ ВНЕШНИЙ ВЕБ-КОНТЕКСТ ===
{web_context}

Подготовь ответ на вопрос пользователя на основе предоставленных документов.

Правила:
1. Релевантные локальные документы используй в первую очередь.
2. Карточка документа подтверждает только его существование, тему, реквизиты и URL.
   Конкретные утверждения о содержании основывай на фрагментах полного текста.
3. Если вопрос о результатах исследования, передавай конкретные выводы,
   оговаривай контекст и ограничения исследования; не придумывай численные значения.
4. Если внешние источники релевантны, допускается дополнить ими ответ,
   но только при наличии соответствующей страницы с конкретным URL.
5. Не путай аналитический доклад с нормативным актом и не представляй
   оценки/сценарии исследователей как обязательные требования.
6. Не показывай служебные метки и названия технологий поиска.
7. В конце обязательно добавь раздел «Источники» с подразделами
   «Локальная база аналитических документов» и (если использовались)
   «Внешние источники».
8. Для каждого реально использованного локального документа приведи
   его название и URL из карточки. Не включай неиспользованные документы.
9. Для каждого внешнего документа приведи название и точный URL из веб-контекста.
   Если URL отсутствует, внешний документ не включай.
10. Перед выдачей проверь, что каждому упомянутому исследованию соответствует
    источник, а каждому источнику — использованная информация в ответе.
11. Если информация из источника НЕ ИСПОЛЬЗУЕТСЯ в ответе, то НЕ ВКЛЮЧАЙ этот источник в итоговый ответ.
""".strip()

    answer = await achat_text(
        system_prompt=ANALYTICAL_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.2,
        max_new_tokens=3200,
    )
    logger.info("Analytical service FINISHED")
    return answer
