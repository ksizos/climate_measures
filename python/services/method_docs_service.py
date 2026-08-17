from __future__ import annotations

import logging

from core.config import (
    LLM_METHOD_DOCS_MODEL,
    METHOD_DOCS_TABLE,
)
from infrastructure.llm.providers.provider_registry import (
    call_method_docs_service_text
)
from prompts.method_docs import (
    METHOD_DOCS_SYSTEM_PROMPT,
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


METHOD_DOCS_ALLOWED_DOMAINS = [
    "economy.gov.ru",
    "government.ru",
    "minprirody.gov.ru",
    "meteorf.gov.ru",
    "rosgidromet.gov.ru",
    "ipcc.ch",
    "unfccc.int",
    "unep.org",
    "undp.org",
]


def generate_method_docs_response(
    user_question: str,
    conversation_history: str | None = None,
) -> str:
    """
    Использует METHOD_DOCS_TABLE, Web Search
    и отдельную NVIDIA-модель.
    """

    logger.info(
        "Method docs service START: %s",
        user_question,
    )

    local_result = retrieve_vector_context(
        user_question,
        table_name=METHOD_DOCS_TABLE,
        top_k=4,
    )

    '''web_result = perform_web_search(
        query=f"""
Найди официальные методические рекомендации,
руководства, доклады и аналитические документы
по следующему вопросу:

{user_question}

Для каждого документа укажи:
- название;
- организацию или автора;
- дату;
- назначение.
""".strip(),
        instructions=(
            "Обязательно используй web_search. "
            "Ищи официальные государственные, "
            "научные и международные документы. "
            "Не утверждай, что найденный документ "
            "является единственным существующим."
        ),
        allowed_domains=(
            METHOD_DOCS_ALLOWED_DOMAINS
        ),
        max_output_tokens=2400,
    )'''
    web_result = perform_web_search(
        query=user_question)
    history_block = ""

    if conversation_history:
        history_block = (
            "История диалога:\n"
            f"{conversation_history}\n\n"
        )
# ПОМЕНЯТЬ ПО ПОВОДУ ИСТОЧНИКОВ!
    final_user_prompt = f"""
{history_block}
Вопрос пользователя:
{user_question}

{local_result.to_context()}

{build_web_facts_context(web_result)}

Подготовь единый ответ.

Правила:
1. Отделяй методические документы от общих публикаций.
2. Не утверждай, что один документ является
   единственным существующим.
3. Используй формулировку:
   «Основным выявленным документом является...»
4. Если другие документы не найдены, пиши:
   «В предоставленном контексте другие документы
   не обнаружены».
5. Не пиши URL.
6. Локальные документы обозначай [LOCAL-N].
7. Веб-источники обозначай [WEB-N].
8. Объясняй применимость каждого документа.
9. Не добавляй собственный раздел со ссылками.
""".strip()

    answer = call_method_docs_service_text(
        user_prompt=final_user_prompt,
        system_prompt=(
            METHOD_DOCS_SYSTEM_PROMPT
        ),
        model=LLM_METHOD_DOCS_MODEL,
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
        "Method docs service FINISHED: "
        "local_documents=%s, web_used=%s, "
        "web_sources=%s",
        len(local_result.documents),
        web_result.used_web_search,
        len(web_result.sources),
    )

    return answer
