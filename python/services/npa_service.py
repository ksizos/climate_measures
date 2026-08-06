from __future__ import annotations

import logging

from core.config import (
    LLM_NPA_MODEL,
    NPA_TABLE,
)
from infrastructure.llm.providers.provider_registry import (
    call_npa_service_text
)
from prompts.npa import (
    NPA_SYSTEM_PROMPT,
)
from services.vector_context_service import (
    append_exact_local_sources,
    retrieve_vector_context,
)
from services.web_search_service import (
    append_exact_web_sources,
    build_web_facts_context,
    perform_web_search,
)

logger = logging.getLogger(__name__)


NPA_ALLOWED_DOMAINS = [
    "publication.pravo.gov.ru",
    "government.ru",
    "economy.gov.ru",
    "minprirody.gov.ru",
    "minjust.gov.ru",
]


def generate_npa_response(
    user_question: str,
    conversation_history: str | None = None,
) -> str:
    """
    Схема работы:

    1. top-4 поиск в NPA_TABLE;
    2. актуальный Yandex Web Search;
    3. объединение контекстов;
    4. итоговый ответ NVIDIA_NPA_MODEL;
    5. точные URL добавляются Python-кодом.
    """

    logger.info(
        "NPA service START: %s",
        user_question,
    )

    local_result = retrieve_vector_context(
        user_question,
        table_name=NPA_TABLE,
        top_k=4,
    )

    web_result = perform_web_search(
        query=f"""
Найди действующие нормативно-правовые акты
по следующему вопросу:

{user_question}

Для каждого документа укажи:
- точное название;
- вид документа;
- номер;
- дату;
- орган власти;
- статус действия.
""".strip(),
        instructions=(
            "Обязательно используй web_search. "
            "Приоритет отдавай официальным "
            "государственным источникам. "
            "Не придумывай документы, даты и номера."
        ),
        allowed_domains=NPA_ALLOWED_DOMAINS,
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

Подготовь единый ответ.

Правила:
1. Учитывай локальную векторную базу и веб-поиск.
2. Веб-поиск используется для проверки актуальности.
3. Не пиши URL: они будут добавлены программно.
4. Локальные документы обозначай [LOCAL-1], [LOCAL-2].
5. Веб-источники обозначай [WEB-1], [WEB-2].
6. Не утверждай, что документ не существует.
7. Если данных нет, пиши:
   «В предоставленном контексте документ не обнаружен».
8. Если данные расходятся, явно опиши расхождение.
9. Не добавляй собственный раздел со ссылками.
""".strip()

    answer = call_npa_service_text(
        user_prompt=final_user_prompt,
        system_prompt=NPA_SYSTEM_PROMPT,
        model=LLM_NPA_MODEL,
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
        "NPA service FINISHED: "
        "local_documents=%s, web_used=%s, "
        "web_sources=%s",
        len(local_result.documents),
        web_result.used_web_search,
        len(web_result.sources),
    )

    return answer
