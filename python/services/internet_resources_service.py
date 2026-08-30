from __future__ import annotations

import asyncio
import logging

from core.config import (
    INTERNET_RESOURCES_TABLE,
)

from infrastructure.llm.provider import (
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
        f"{user_question} "
        "- предоставь ии-обзор "
        "по вопросу. контекст - экология, изменения климата, адаптация к изменениям климата"
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

=== РЕЗУЛЬТАТЫ ВНЕШНЕГО ВЕБ-ПОИСКА ===

{web_result.to_context()}

Подготовь структурированный ответ.

При необходимости используй разделы:

### Официальные российские ресурсы

### Официальные международные ресурсы

### Дополнительные аналитические материалы

Не создавай пустые разделы.

Правила:

1. Используй релевантные ресурсы
   из локальной базы.

2. Дополнительно используй
   релевантные внешние ресурсы,
   только если для них передан
   конкретный URL.

3. Не рекомендуй ресурс,
   если для него невозможно определить URL.

4. Не дублируй один и тот же ресурс,
   если он найден и локально,
   и во внешнем поиске.
   В таком случае используй локальную запись.

5. Для каждого ресурса,
   включённого в основной ответ,
   обязательно укажи его URL
   непосредственно рядом с описанием ресурса.

6. Не пиши:
   "URL не указан",
   "URL отсутствует",
   "ссылка отсутствует".

   Если URL нет,
   не включай ресурс в ответ.

7. Не придумывай названия,
   организации, функции или URL.

8. В конце добавь:

### Источники

**Локальная база ресурсов**

Перечисли только локальные ресурсы,
которые действительно рекомендованы
в основном ответе.

**Внешний веб-поиск**

Перечисли только внешние ресурсы,
которые действительно рекомендованы
в основном ответе.

9. У каждого источника
   обязательно должны быть:
   - название;
   - URL.

10. Не показывай пользователю
    никакие внутренние технические
    идентификаторы источников.

11. Перед отправкой ответа проверь:

    каждый ресурс в основном ответе
    -> имеет URL;

    каждый ресурс в основном ответе
    -> присутствует в источниках;

    каждый источник
    -> присутствует в основном ответе;

    в тексте нет технических идентификаторов.
    12. КРИТИЧЕСКОЕ ПРАВИЛО:

Любой ресурс разрешено включать
в основной ответ и в раздел "Источники"
ТОЛЬКО если для него в переданном контексте
явно присутствует непустой URL.

Если URL для ресурса отсутствует —
полностью исключи этот ресурс из ответа.

Запрещено писать:
"URL не указан",
"URL отсутствует",
"ссылка отсутствует".

Правило наличия URL имеет приоритет
над всеми правилами о полноте ответа
и добавлении релевантных ресурсов.

13. Перед отправкой ответа удали
все ресурсы, возле которых ты не можешь
дословно указать URL из переданного контекста.
14. Внутренние обозначения:
    WEB-1
    LOCAL-1
    LOCAL-2
    и подобные

    являются только
    техническими метками контекста.

    НИКОГДА не показывай эти обозначения пользователю
    Также НЕ ПИШИ название таблицы xlsx, откуда взята информация (НЕ ПИШИ INTERNET_TABLE.xlsx, НЕ ПИШИ LOCAL-1 и т.д.)
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