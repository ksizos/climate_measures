from __future__ import annotations

import asyncio
import logging

from core.config import NPA_TABLE

from infrastructure.llm.local_yandex import (
    achat_text,
)

from prompts.npa import (
    NPA_SYSTEM_PROMPT,
)

from services.vector_context_service import (
    retrieve_vector_context,
)

from services.web_search_service import (
    perform_web_search,
)


logger = logging.getLogger(__name__)


async def generate_npa_response(
    user_question: str,
    conversation_history: str | None = None,
) -> str:
    """
    Схема:

    RAG ───────────┐
                   ├─> Local YandexGPT
    Google AI ─────┘

    RAG и web search независимы
    и выполняются параллельно.
    """

    logger.info(
        "NPA service START: %s",
        user_question,
    )

    web_query = (
        "действующие нормативные правовые акты "
        "Россия климатические риски адаптация "
        f"{user_question}"
    )

    local_task = asyncio.to_thread(
        retrieve_vector_context,
        user_question,
        table_name=NPA_TABLE,
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

    final_user_prompt = f"""
{history_block}

Вопрос пользователя:
{user_question}

=== ЛОКАЛЬНАЯ БАЗА НПА ===

{local_result.to_context()}

=== GOOGLE AI OVERVIEW ===

{web_result.to_context()}

Подготовь единый экспертный ответ на вопрос пользователя.

Правила:

1. Используй локальную базу и Google AI Overview
   как информационный контекст.

2. Для нормативно-правовых утверждений
   приоритет отдавай первичным и официальным документам.

3. Google AI Overview используй для дополнительной
   информации и проверки актуального контекста.

4. Не придумывай:
   - документы;
   - номера документов;
   - даты;
   - органы власти;
   - статусы документов;
   - URL.

5. Если нужный документ отсутствует
   в предоставленных данных, не утверждай,
   что такого документа вообще не существует.
   Пиши:
   "В предоставленном контексте документ не обнаружен".

6. Если локальный и веб-контекст расходятся,
   явно укажи на расхождение.

7. Не упоминай внутренние идентификаторы
   LOCAL-N и WEB-N в основном тексте,
   если они не нужны для понимания ответа.

8. В конце обязательно добавь раздел:

### Источники

9. В этот раздел включай ТОЛЬКО источники,
   сведения из которых реально использованы
   при формировании ответа.

10. Не включай источник только потому,
    что он присутствовал в контексте.

11. Для локальных источников разрешено использовать
    только URL из блоков [LOCAL-N].

12. Для веб-источников разрешено использовать
    только URL из блоков [WEB-N].

13. Копируй URL дословно.
    Не изменяй ни одного символа.

14. Не придумывай отсутствующие URL.
""".strip()

    answer = await achat_text(
        system_prompt=NPA_SYSTEM_PROMPT,
        user_prompt=final_user_prompt,
        temperature=0.2,
        max_new_tokens=2800,
    )

    logger.info(
        "NPA service FINISHED: "
        "local_documents=%s, "
        "web_overview=%s, "
        "web_sources=%s",
        len(local_result.documents),
        bool(web_result.overview),
        len(web_result.sources),
    )

    return answer