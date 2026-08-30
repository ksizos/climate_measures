from __future__ import annotations

import asyncio
import logging

from dataclasses import (
    dataclass,
    field,
)
from typing import Any

from core.config import (
    NPA_TABLE,
)

from infrastructure.llm.provider import (
    achat_text,
)

from prompts.npa import (
    NPA_SYSTEM_PROMPT,
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


NPA_CATALOG_TOP_K = 3

NPA_CONTENT_TOP_K_PER_DOCUMENT = 2


# =====================================================
# LOCAL NPA RAG RESULT
# =====================================================

@dataclass(slots=True)
class NpaLocalContextResult:

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
                "В локальной базе НПА "
                "релевантные документы "
                "не найдены."
            )

        parts: list[str] = []

        parts.append(
            "=== КАРТОЧКИ "
            "НАЙДЕННЫХ НПА ==="
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

            npa_id = (
                metadata.get(
                    "npa_id"
                )
            )

            document_key = str(
                npa_id
            )

            title = str(
                metadata.get(
                    "title",
                    "",
                )
            ).strip()

            document_type = str(
                metadata.get(
                    "document_type",
                    "",
                )
            ).strip()

            authority = str(
                metadata.get(
                    "authority",
                    "",
                )
            ).strip()

            number = str(
                metadata.get(
                    "number",
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
                    f"[NPA-DOC-"
                    f"{doc_index}]"
                )
            ]

            if document_type:
                block.append(
                    "Вид документа: "
                    f"{document_type}"
                )

            if authority:
                block.append(
                    "Орган: "
                    f"{authority}"
                )

            if number:
                block.append(
                    "Номер: "
                    f"{number}"
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
            # Chunks этого же документа
            # ----------------------------------

            chunks = (
                self
                .content_documents
                .get(
                    document_key,
                    [],
                )
            )

            if not chunks:
                parts.append(
                    (
                        f"[NPA-DOC-"
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
                        f"[NPA-DOC-"
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
# TWO-STAGE LOCAL NPA RETRIEVAL
# =====================================================

def retrieve_npa_local_context(
    query: str,
) -> NpaLocalContextResult:

    logger.info(
        "NPA local retrieval START: %s",
        query,
    )

    # -------------------------------------
    # STAGE 1:
    # ищем только карточки документов
    # -------------------------------------

    catalog_result = (
        retrieve_vector_context(
            query,
            table_name=NPA_TABLE,
            top_k=(
                NPA_CATALOG_TOP_K
            ),
            metadata_filters={
                "record_type":
                    "catalog",
            },
        )
    )

    result = (
        NpaLocalContextResult(
            catalog_documents=(
                catalog_result.documents
            )
        )
    )

    selected_ids: list[
        Any
    ] = []

    # -------------------------------------
    # STAGE 2:
    # для каждого найденного документа
    # ищем только его content chunks
    # -------------------------------------

    for catalog_document in (
        catalog_result.documents
    ):

        npa_id = (
            catalog_document
            .metadata
            .get(
                "npa_id"
            )
        )

        if npa_id is None:
            logger.warning(
                "NPA catalog result "
                "without npa_id"
            )
            continue

        selected_ids.append(
            npa_id
        )

        content_result = (
            retrieve_vector_context(
                query,
                table_name=NPA_TABLE,
                top_k=(
                    NPA_CONTENT_TOP_K_PER_DOCUMENT
                ),
                metadata_filters={
                    "record_type":
                        "content",

                    "npa_id":
                        str(npa_id),
                },
            )
        )

        result.content_documents[
            str(npa_id)
        ] = (
            content_result.documents
        )

    logger.info(
        "NPA local retrieval FINISHED: "
        "documents=%s, "
        "content_chunks=%s, "
        "document_ids=%s",
        len(
            result.catalog_documents
        ),
        result.content_count,
        selected_ids,
    )

    return result


# =====================================================
# NPA AGENT
# =====================================================

async def generate_npa_response(
    user_question: str,
    conversation_history:
        str | None = None,
) -> str:

    logger.info(
        "NPA service START: %s",
        user_question,
    )

    web_query = (
        f"{user_question} "
        "- предоставь ии-обзор "
        "по вопросу"
    )

    # Полный двухэтапный локальный RAG
    # идёт параллельно с web search.
    local_task = asyncio.to_thread(
        retrieve_npa_local_context,
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

    final_user_prompt = f"""
{history_block}

Вопрос пользователя:
{user_question}

=== ЛОКАЛЬНАЯ БАЗА НПА ===

{local_context}

=== GOOGLE AI OVERVIEW ===

{web_result.to_context()}

Подготовь единый экспертный ответ
на вопрос пользователя.

Правила:

1. Используй локальную базу НПА
   как приоритетный источник
   для документов, которые
   в ней присутствуют.

2. Карточки [NPA-DOC-N]
   подтверждают существование документа
   и его реквизиты:
   вид, орган, номер, дату,
   название и официальный URL.

3. Фрагменты
   [NPA-DOC-N-CONTENT-M]
   содержат полный текст документа.

4. Утверждения о том,
   что НПА что-либо устанавливает,
   требует, предписывает,
   определяет или регулирует,
   делай прежде всего
   на основании фрагментов
   полного текста документа.

5. Не делай подробных выводов
   о содержании НПА
   только по его названию.

6. Google AI Overview используй
   как дополнительный источник
   актуального контекста.

7. Не придумывай:
   - документы;
   - номера;
   - даты;
   - органы власти;
   - содержание документов;
   - статусы;
   - URL.

8. Если нужного документа
   нет в переданном контексте,
   не утверждай,
   что такого документа
   вообще не существует.

9. Если локальный
   и веб-контекст расходятся,
   явно укажи на расхождение.

10. В основном тексте
    не упоминай внутренние обозначения
    NPA-DOC и CONTENT.

11. В конце обязательно добавь:

### Источники

12. Включай только источники,
    сведения из которых реально
    использованы в ответе.

13. Для локального НПА
    URL бери только
    из его блока [NPA-DOC-N].

14. Копируй URL дословно.
    Не изменяй ни одного символа.

15. Если URL отсутствует,
    не придумывай его.
""".strip()

    answer = await achat_text(
        system_prompt=(
            NPA_SYSTEM_PROMPT
        ),
        user_prompt=(
            final_user_prompt
        ),
        temperature=0.2,
        max_new_tokens=2800,
    )

    logger.info(
        "NPA service FINISHED: "
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