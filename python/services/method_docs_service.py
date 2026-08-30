from __future__ import annotations

import asyncio
import logging

from dataclasses import (
    dataclass,
    field,
)

from typing import Any

from core.config import (
    METHOD_DOCS_TABLE,
)

from infrastructure.llm.provider import (
    achat_text,
)

from prompts.method_docs import (
    METHOD_DOCS_SYSTEM_PROMPT,
)

from services.vector_context_service import (
    RetrievedVectorDocument,
    retrieve_vector_context,
)

from services.web_search_service import (
    perform_web_search,
)


logger = logging.getLogger(
    __name__
)


METHOD_CATALOG_TOP_K = 3

METHOD_CONTENT_TOP_K_PER_DOCUMENT = 2


# =====================================================
# LOCAL METHOD CONTEXT RESULT
# =====================================================

@dataclass(slots=True)
class MethodLocalContextResult:

    catalog_documents: list[
        RetrievedVectorDocument
    ] = field(
        default_factory=list
    )

    content_documents: dict[
        str,
        list[
            RetrievedVectorDocument
        ],
    ] = field(
        default_factory=dict
    )

    @property
    def content_count(
        self,
    ) -> int:

        return sum(
            len(documents)
            for documents
            in self
            .content_documents
            .values()
        )

    def to_context(
        self,
    ) -> str:

        if not self.catalog_documents:

            return (
                "В локальной базе "
                "методических документов "
                "релевантные документы "
                "не найдены."
            )

        parts: list[str] = []

        parts.append(
            "=== КАРТОЧКИ НАЙДЕННЫХ "
            "МЕТОДИЧЕСКИХ ДОКУМЕНТОВ ==="
        )

        for doc_index, document in (
            enumerate(
                self.catalog_documents,
                start=1,
            )
        ):

            metadata = (
                document.metadata
                or {}
            )

            method_id = (
                metadata.get(
                    "method_id"
                )
            )

            method_key = str(
                method_id
            )

            title = str(
                metadata.get(
                    "title",
                    "",
                )
            ).strip()

            form = str(
                metadata.get(
                    "form",
                    "",
                )
            ).strip()

            date = str(
                metadata.get(
                    "date",
                    "",
                )
            ).strip()

            url = str(
                metadata.get(
                    "url",
                    "",
                )
            ).strip()

            block: list[str] = [
                (
                    f"[METHOD-DOC-"
                    f"{doc_index}]"
                )
            ]

            if form:
                block.append(
                    "Форма документа: "
                    f"{form}"
                )

            if date:
                block.append(
                    "Дата: "
                    f"{date}"
                )

            if title:
                block.append(
                    "Название: "
                    f"{title}"
                )

            if url:
                block.append(
                    "URL: "
                    f"{url}"
                )

            if (
                document.score
                is not None
            ):
                block.append(
                    "Релевантность "
                    "карточки: "
                    f"{document.score:.4f}"
                )

            parts.append(
                "\n".join(
                    block
                )
            )

            # ----------------------------------
            # CONTENT этого же документа
            # ----------------------------------

            chunks = (
                self
                .content_documents
                .get(
                    method_key,
                    [],
                )
            )

            if not chunks:

                parts.append(
                    (
                        f"[METHOD-DOC-"
                        f"{doc_index}"
                        "-CONTENT]"
                        "\n"
                        "Полный текст "
                        "этого документа "
                        "в локальной базе "
                        "не найден "
                        "или релевантные "
                        "фрагменты "
                        "не обнаружены."
                    )
                )

                continue

            for chunk_index, chunk in (
                enumerate(
                    chunks,
                    start=1,
                )
            ):

                chunk_metadata = (
                    chunk.metadata
                    or {}
                )

                page_label = (
                    chunk_metadata.get(
                        "page_label"
                    )
                    or
                    chunk_metadata.get(
                        "page_number"
                    )
                )

                chunk_block = [
                    (
                        f"[METHOD-DOC-"
                        f"{doc_index}"
                        "-CONTENT-"
                        f"{chunk_index}]"
                    )
                ]

                if title:
                    chunk_block.append(
                        "Документ: "
                        f"{title}"
                    )

                if page_label:
                    chunk_block.append(
                        "Страница: "
                        f"{page_label}"
                    )

                chunk_block.append(
                    "Фрагмент "
                    "полного текста:\n"
                    f"{chunk.text}"
                )

                if (
                    chunk.score
                    is not None
                ):
                    chunk_block.append(
                        "Релевантность "
                        "фрагмента: "
                        f"{chunk.score:.4f}"
                    )

                parts.append(
                    "\n".join(
                        chunk_block
                    )
                )

        return (
            "\n\n---\n\n"
            .join(parts)
        )


# =====================================================
# TWO-STAGE METHOD RETRIEVAL
# =====================================================

def retrieve_method_local_context(
    query: str,
) -> MethodLocalContextResult:

    logger.info(
        "Method local retrieval START: %s",
        query,
    )

    # -----------------------------------------
    # STAGE 1:
    # поиск только по карточкам
    # -----------------------------------------

    catalog_result = (
        retrieve_vector_context(
            query,
            table_name=(
                METHOD_DOCS_TABLE
            ),
            top_k=(
                METHOD_CATALOG_TOP_K
            ),
            metadata_filters={
                "record_type":
                    "catalog",
            },
        )
    )

    result = (
        MethodLocalContextResult(
            catalog_documents=(
                catalog_result.documents
            )
        )
    )

    selected_ids: list[Any] = []

    # -----------------------------------------
    # STAGE 2:
    # поиск внутри каждого документа
    # -----------------------------------------

    for catalog_document in (
        catalog_result.documents
    ):

        method_id = (
            catalog_document
            .metadata
            .get(
                "method_id"
            )
        )

        if method_id is None:

            logger.warning(
                "METHOD catalog result "
                "without method_id"
            )

            continue

        # На всякий случай
        # принудительно строка.
        method_id = str(
            method_id
        )

        selected_ids.append(
            method_id
        )

        logger.info(
            "METHOD content search: "
            "method_id=%r, type=%s",
            method_id,
            type(method_id).__name__,
        )

        content_result = (
            retrieve_vector_context(
                query,
                table_name=(
                    METHOD_DOCS_TABLE
                ),
                top_k=(
                    METHOD_CONTENT_TOP_K_PER_DOCUMENT
                ),
                metadata_filters={
                    "record_type":
                        "content",

                    "method_id":
                        method_id,
                },
            )
        )

        result.content_documents[
            method_id
        ] = (
            content_result.documents
        )

    logger.info(
        "Method local retrieval FINISHED: "
        "documents=%s, "
        "content_chunks=%s, "
        "method_ids=%s",
        len(
            result.catalog_documents
        ),
        result.content_count,
        selected_ids,
    )

    return result


# =====================================================
# METHOD DOCS AGENT
# =====================================================

async def generate_method_docs_response(
    user_question: str,
    conversation_history:
        str | None = None,
) -> str:

    logger.info(
        "Method docs service START: %s",
        user_question,
    )

    web_query = (
        "официальные методические рекомендации "
        "руководства доклады аналитические документы "
        "климатические риски адаптация "
        f"{user_question}"
    )

    # Двухступенчатый локальный RAG
    # и веб-поиск выполняются параллельно.

    local_task = asyncio.to_thread(
        retrieve_method_local_context,
        user_question,
    )

    web_task = asyncio.to_thread(
        perform_web_search,
        web_query,
    )

    (
        local_result,
        web_result,
    ) = await asyncio.gather(
        local_task,
        web_task,
    )

    history_block = ""

    if conversation_history:

        history_block = f"""
История диалога:
{conversation_history}
""".strip()

    local_context = (
        local_result.to_context()
    )

    user_prompt = f"""
{history_block}

Вопрос пользователя:
{user_question}

=== ЛОКАЛЬНАЯ БАЗА МЕТОДИЧЕСКИХ ДОКУМЕНТОВ ===

{local_context}

=== РЕЗУЛЬТАТЫ ВНЕШНЕГО ВЕБ-ПОИСКА ===

{web_result.to_context()}

Подготовь единый экспертный ответ.

Правила:

1. Локальная база содержит два типа данных:

   а) карточки методических документов;
   б) фрагменты полного текста документов.

2. Карточки [METHOD-DOC-N]
   подтверждают существование документа
   и его реквизиты:
   форму, дату, название и URL.

3. Фрагменты
   [METHOD-DOC-N-CONTENT-M]
   содержат непосредственно
   текст выбранного документа.

4. Утверждения о содержании документа,
   его методике, требованиях,
   этапах, формулах, показателях,
   процедурах или рекомендациях
   делай прежде всего
   на основании фрагментов
   полного текста.

5. Не делай подробных выводов
   о содержании документа
   только на основании его названия.

6. Локальная база является
   приоритетным источником
   для документов,
   которые в ней присутствуют.

7. При этом не игнорируй
   полезные результаты
   внешнего веб-поиска.

8. Внешние источники используй,
   если они:
   - содержат дополнительные
     релевантные документы;
   - дают актуальный контекст;
   - уточняют сведения,
     отсутствующие локально;
   - дополняют содержание ответа.

9. Не придумывай:
   - документы;
   - организации;
   - авторов;
   - даты;
   - содержание;
   - URL.

10. Не утверждай,
    что найденный документ
    является единственным
    существующим.

11. Если полный текст документа
    отсутствует,
    можно сообщить его реквизиты,
    но не придумывай его содержание.

12. Внутренние обозначения:

    METHOD-DOC
    METHOD-DOC-1
    METHOD-DOC-1-CONTENT-1
    CONTENT

    являются только
    техническими метками контекста.

    НИКОГДА не показывай
    эти обозначения пользователю:
    ни в основном тексте,
    ни в заголовках,
    ни в списках,
    ни в источниках.

13. В конце добавь:

### Источники

14. Источники разделяй
    по происхождению.

Если использовалась локальная база:

**Локальная база методических документов**

Формат:

- Форма документа — название — дата — URL

15. Если использовались
    результаты веб-поиска:

**Внешние источники**

Формат:

- Организация или ресурс —
  название материала — URL

16. Если источники определённого
    типа не использовались,
    соответствующий подраздел
    не создавай.

17. Для локальных документов
    URL бери только
    из соответствующей карточки
    [METHOD-DOC-N].

18. Для внешних источников
    URL бери только
    из результатов веб-поиска.

19. Не называй
    Google AI Overview источником.

    Источниками являются
    конкретные страницы,
    URL которых присутствуют
    во внешнем контексте.

20. Включай только те источники,
    информация из которых
    действительно использована
    в ответе.

21. Копируй URL дословно.

22. Не переноси URL
    одного документа
    к другому документу.
""".strip()

    answer = await achat_text(
        system_prompt=(
            METHOD_DOCS_SYSTEM_PROMPT
        ),
        user_prompt=user_prompt,
        temperature=0.2,
        max_new_tokens=2800,
    )

    logger.info(
        "Method docs service FINISHED: "
        "catalog_documents=%s, "
        "content_chunks=%s, "
        "web_overview=%s, "
        "web_sources=%s",
        len(
            local_result
            .catalog_documents
        ),
        local_result.content_count,
        bool(
            web_result.overview
        ),
        len(
            web_result.sources
        ),
    )

    return answer