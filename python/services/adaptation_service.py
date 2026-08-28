from __future__ import annotations

import logging

from core.config import (
    ADAPTATION_TABLE,
)

from infrastructure.llm.provider import (
    chat_text,
)

from prompts.adaptation import (
    RAG_SYSTEM_PROMPT,
)

from services.vector_context_service import (
    retrieve_vector_context,
)


logger = logging.getLogger(__name__)


def generate_adaptation_response(
    user_question: str,
    conversation_history: str | None = None,
) -> str:
    """
    Схема:

    RAG
     ↓
    Local YandexGPT
    """

    logger.info(
        "Adaptation service START: %s",
        user_question,
    )

    local_result = retrieve_vector_context(
        user_question,
        table_name=ADAPTATION_TABLE,
        top_k=4,
    )

    history_block = ""

    if conversation_history:
        history_block = f"""
История диалога:
{conversation_history}
""".strip()

    user_prompt = f"""
{history_block}

Вопрос пользователя:
{user_question}

=== ЛОКАЛЬНАЯ БАЗА АДАПТАЦИОННЫХ МЕРОПРИЯТИЙ ===

{local_result.to_context()}

Сформируй экспертный ответ на вопрос пользователя.

Правила:

1. Основывай рекомендации на переданном контексте.

2. Не придумывай мероприятия,
   которых нет в контексте,
   как будто они взяты из базы.

3. Учитывай территорию,
   климатический риск,
   отрасль и другие условия,
   если они присутствуют в запросе.

4. Объясняй, почему предложенное
   мероприятие подходит пользователю.

5. В конце добавь:

### Источники

6. Включай только источники,
   сведения или мероприятия из которых
   реально использованы в ответе.

7. URL бери исключительно
   из блоков [LOCAL-N].

8. Копируй URL дословно.

9. Если у использованного документа
   URL отсутствует,
   не придумывай его.
""".strip()

    answer = chat_text(
        system_prompt=RAG_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.2,
        max_new_tokens=2800,
    )

    logger.info(
        "Adaptation service FINISHED: "
        "local_documents=%s",
        len(local_result.documents),
    )

    return answer