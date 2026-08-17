from __future__ import annotations

import logging

from core.config import (
    INTERNET_RESOURCES_TABLE,
    LLM_INTERNET_RESOURCES_MODEL,
)
from infrastructure.llm.providers.provider_registry import (
    call_internet_resources_service_text
)
from prompts.internet_resources import (
    INTERNET_RESOURCES_SYSTEM_PROMPT,
)
from services.vector_context_service import (
    append_exact_local_sources,
    retrieve_vector_context,
)
from services.web_search_service import (
    #append_exact_web_sources,
    #build_web_facts_context,
    perform_web_search,
)


logger = logging.getLogger(__name__)


OFFICIAL_RESOURCE_DOMAINS = [
    # Российские официальные ресурсы
    "economy.gov.ru",
    "government.ru",
    "meteorf.gov.ru",
    "rosgidromet.gov.ru",
    "cbr.ru",

    # Международные официальные ресурсы
    "ipcc.ch",
    "unfccc.int",
    "unep.org",
    "undp.org",
    "worldbank.org",
    "climateknowledgeportal.worldbank.org",
]

# АСИНХРОННО?
def generate_internet_resources_response(
    user_question: str,
    conversation_history: str | None = None,
) -> str:
    """
    Использует локальную таблицу ресурсов
    и актуальный Web Search.
    """

    logger.info(
        "Internet resources service START: %s",
        user_question,
    )

    local_result = retrieve_vector_context(
        user_question,
        table_name=INTERNET_RESOURCES_TABLE,
        top_k=4,
    )

    web_result = perform_web_search(
        query=f"""
Найди официальные российские и международные
порталы, базы данных и информационные системы
по следующему вопросу:

{user_question}

Раздели найденное на:
1. официальные российские ресурсы;
2. официальные международные ресурсы.

Не включай научные статьи, частные издательства
и агрегаторы в официальные категории.
""".strip(),
        instructions=(
            "Обязательно используй web_search. "
            "Ищи официальные ресурсы государственных "
            "органов и международных организаций."
        ),
        allowed_domains=(
            OFFICIAL_RESOURCE_DOMAINS
        ),
        max_output_tokens=2400,
    )

    history_block = ""

    if conversation_history:
        history_block = (
            "История диалога:\n"
            f"{conversation_history}\n\n"
        )

    final_user_prompt = f"""
{history_block}
Вопрос пользователя:
{user_question}

{local_result.to_context()}

{build_web_facts_context(web_result)}

Подготовь ответ с разделами:

### Официальные российские ресурсы
### Официальные международные ресурсы
### Дополнительные аналитические материалы

Правила:
1. Не помещай научные статьи и частные сайты
   в официальные категории.
2. Не пиши URL.
3. Локальные ресурсы обозначай [LOCAL-N].
4. Веб-источники обозначай [WEB-N].
5. Не дублируй одинаковые ресурсы.
6. Для каждого ресурса объясни его назначение.
7. Не добавляй собственный раздел со ссылками.
""".strip()

    answer = call_internet_resources_service_text(
        user_prompt=final_user_prompt,
        system_prompt=(
            INTERNET_RESOURCES_SYSTEM_PROMPT
        ),
        model=(
            LLM_INTERNET_RESOURCES_MODEL
        ),
        temperature=0.2,
        max_output_tokens=2800,
    )

    answer = append_exact_local_sources(
        answer,
        local_result,
    )

    answer = append_exact_web_sources(
        answer,
        web_result,
    )

    logger.info(
        "Internet resources service FINISHED: "
        "local_documents=%s, web_used=%s, "
        "web_sources=%s",
        len(local_result.documents),
        web_result.used_web_search,
        len(web_result.sources),
    )

    return answer
