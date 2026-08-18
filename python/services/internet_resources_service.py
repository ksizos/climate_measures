from __future__ import annotations

import asyncio
import logging

from core.config import (
    INTERNET_RESOURCES_TABLE,
)

from infrastructure.llm.local_yandex import (
    achat_text,
)

from prompts.internet_resources import (
    INTERNET_RESOURCES_SYSTEM_PROMPT,
)

from services.vector_context_service import (
    retrieve_vector_context,
)

from services.web_search_service import (
    perform_web_search,
)


logger = logging.getLogger(__name__)


async def generate_internet_resources_response(
    user_question: str,
    conversation_history: str | None = None,
) -> str:
    """
    Параллельно:
    - локальная база ресурсов;
    - Google AI Overview.

    Затем один итоговый вызов YandexGPT.
    """

    logger.info(
        "Internet resources service START: %s",
        user_question,
    )

    web_query = (
        "официальные российские и международные "
        "порталы базы данных информационные системы "
        "климатические риски адаптация "
        f"{user_question}"
    )

    local_task = asyncio.to_thread(
        retrieve_vector_context,
        user_question,
        table_name=INTERNET_RESOURCES_TABLE,
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

=== ЛОКАЛЬНАЯ БАЗА ИНТЕРНЕТ-РЕСУРСОВ ===

{local_result.to_context()}

=== GOOGLE AI OVERVIEW ===

{web_result.to_context()}

Подготовь структурированный ответ.

При необходимости используй разделы:

### Официальные российские ресурсы

### Официальные международные ресурсы

### Дополнительные аналитические материалы

Не создавай пустые разделы.

Правила:

1. Не помещай частные сайты,
   коммерческие публикации и обычные статьи
   в категорию официальных ресурсов.

2. Для каждого рекомендуемого ресурса
   кратко объясни его назначение
   и пользу для вопроса пользователя.

3. Не дублируй одинаковые ресурсы.

4. Не придумывай организации,
   ресурсы или URL.

5. В конце обязательно добавь:

### Источники

6. Включай в источники только ресурсы,
   реально использованные или рекомендованные
   в основном ответе.

7. Разрешено использовать только URL,
   переданные в блоках [LOCAL-N]
   и [WEB-N].

8. URL копируй дословно.

9. Не добавляй источник только потому,
   что Google указал его в AI Overview.
   Он должен реально использоваться
   в сформированном ответе.
""".strip()

    answer = await achat_text(
        system_prompt=(
            INTERNET_RESOURCES_SYSTEM_PROMPT
        ),
        user_prompt=user_prompt,
        temperature=0.2,
        max_new_tokens=2800,
    )

    logger.info(
        "Internet resources service FINISHED: "
        "local_documents=%s, "
        "web_overview=%s, "
        "web_sources=%s",
        len(local_result.documents),
        bool(web_result.overview),
        len(web_result.sources),
    )

    return answer