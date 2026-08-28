from __future__ import annotations

import asyncio
import logging

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
    retrieve_vector_context,
)

from services.web_search_service import (
    perform_web_search,
)


logger = logging.getLogger(__name__)


async def generate_method_docs_response(
    user_question: str,
    conversation_history: str | None = None,
) -> str:
    """
    Параллельно:
    - METHOD_DOCS_TABLE;
    - Google AI Overview.

    После этого один вызов YandexGPT.
    """

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

    local_task = asyncio.to_thread(
        retrieve_vector_context,
        user_question,
        table_name=METHOD_DOCS_TABLE,
        top_k=4,
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

    user_prompt = f"""
{history_block}

Вопрос пользователя:
{user_question}

=== ЛОКАЛЬНАЯ БАЗА МЕТОДИЧЕСКИХ ДОКУМЕНТОВ ===

{local_result.to_context()}

=== GOOGLE AI OVERVIEW ===

{web_result.to_context()}

Подготовь единый экспертный ответ.

Правила:

1. Отделяй официальные методические документы
   от обычных информационных публикаций.

2. Не придумывай документы,
   организации, авторов, даты или URL.

3. Не утверждай, что найденный документ
   является единственным существующим.

4. Если в контексте найден только один
   релевантный документ, можно написать:
   "Основным выявленным документом является..."

5. Если другие документы отсутствуют, пиши:
   "В предоставленном контексте другие
   релевантные документы не обнаружены".

6. Объясняй назначение и применимость
   документов относительно вопроса пользователя.

7. Локальная база является приоритетным
   источником для имеющихся в ней документов.

8. Google AI Overview используй
   как дополнительный актуальный контекст.

9. В конце обязательно добавь:

### Источники

10. Включай только источники,
    реально использованные в ответе.

11. Разрешены только URL,
    присутствующие в [LOCAL-N]
    или [WEB-N].

12. Копируй URL дословно.

13. Не добавляй найденный источник,
    если информация из него
    не использовалась в ответе.
""".strip()

    answer = await achat_text(
        system_prompt=METHOD_DOCS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.2,
        max_new_tokens=2800,
    )

    logger.info(
        "Method docs service FINISHED: "
        "local_documents=%s, "
        "web_overview=%s, "
        "web_sources=%s",
        len(local_result.documents),
        bool(web_result.overview),
        len(web_result.sources),
    )

    return answer