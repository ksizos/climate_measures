from __future__ import annotations

import logging

from llama_index.core.llms import (
    ChatMessage,
)

from core.config import (
    ADAPTATION_TABLE,
    LLM_ADAPTATION_MODEL,
)

from infrastructure.llm.providers.provider_registry import (
    get_adaptation_service_llm
)

from infrastructure.vector_store.pgvector import (
    load_vector_index,
)
from prompts.adaptation import (
    RAG_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)

META_COLUMNS_DISPLAY = {
    "meta_Наименование района": (
        "Наименование района"
    ),
    "meta_Агроклиматические условия района": (
        "Агроклиматические условия района"
    ),
    "meta_Ответственная организация": (
        "Ответственная организация"
    ),
    "meta_Источник": "Источник",
}


adaptation_llm = get_adaptation_service_llm(
    model=LLM_ADAPTATION_MODEL,
    temperature=0.2,
    max_tokens=2800,
    function_calling=False,
)


def retrieve_rag_context(
    user_question: str,
) -> str:
    try:
        index = load_vector_index(
            table_name=ADAPTATION_TABLE,
        )

        retriever = index.as_retriever(
            similarity_top_k=4,
        )

        nodes = retriever.retrieve(
            user_question
        )

        logger.info(
            "Adaptation RAG: query=%s, nodes=%s",
            user_question[:300],
            len(nodes),
        )

        if not nodes:
            return (
                "Не найдено релевантных документов."
            )

        context_parts: list[str] = []

        for index_number, node in enumerate(
            nodes,
            start=1,
        ):
            block = [
                f"[LOCAL-{index_number}]",
                node.get_content().strip(),
            ]

            for (
                metadata_key,
                display_name,
            ) in META_COLUMNS_DISPLAY.items():
                value = node.metadata.get(
                    metadata_key
                )

                if value:
                    block.append(
                        f"{display_name}: {value}"
                    )

            score = getattr(
                node,
                "score",
                None,
            )

            if score is not None:
                block.append(
                    "Релевантность: "
                    f"{float(score):.4f}"
                )

            context_parts.append(
                "\n".join(block)
            )

        return "\n\n---\n\n".join(
            context_parts
        )

    except Exception as error:
        logger.exception(
            "Ошибка при извлечении "
            "адаптационного RAG-контекста"
        )

        return (
            "Ошибка при извлечении контекста: "
            f"{error}"
        )


def generate_adaptation_response(
    user_question: str,
    conversation_history: str | None = None,
) -> str:
    context = retrieve_rag_context(
        user_question
    )

    history_instruction = ""

    if conversation_history:
        history_instruction = (
            "\n\nИстория диалога:\n"
            f"{conversation_history}\n\n"
            "Учитывай историю при формировании ответа."
        )

    full_system_prompt = (
        RAG_SYSTEM_PROMPT
        + history_instruction
        + "\n\nКонтекст из базы знаний:\n"
        + context
    )

    messages = [
        ChatMessage(
            role="system",
            content=full_system_prompt,
        ),
        ChatMessage(
            role="user",
            content=(
                "Пользовательский запрос: "
                f"{user_question}"
            ),
        ),
    ]

    response = adaptation_llm.chat(
        messages
    )

    return (
        response.message.content
        or ""
    )
