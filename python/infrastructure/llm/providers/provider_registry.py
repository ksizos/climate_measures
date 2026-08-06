from __future__ import annotations

from collections.abc import Callable
from typing import Any

from core.config import (
    LLM_ADAPTATION_PROVIDER,
    LLM_DIALOG_PROVIDER,
    LLM_INTERNET_RESOURCES_PROVIDER,
    LLM_METHOD_DOCS_PROVIDER,
    LLM_NPA_PROVIDER,
    LLM_ORCHESTRATOR_PROVIDER,
    LLM_SPECIALIZED_AGENT_PROVIDER,
    LLM_STATISTICS_ANSWER_PROVIDER,
    LLM_STATISTICS_SQL_PROVIDER,
    LLM_STRUCTURED_DATA_PROVIDER,
)
from infrastructure.llm.providers.nvidia import (
    call_nvidia_text,
    get_nvidia_llm,
)
from infrastructure.llm.providers.openrouter import (
    call_openrouter_text,
    get_openrouter_llm,
)


LLMFactory = Callable[..., Any]
TextCall = Callable[..., str]


LLM_FACTORIES: dict[str, LLMFactory] = {
    "nvidia": get_nvidia_llm,
    "openrouter": get_openrouter_llm,
}

TEXT_CALLS: dict[str, TextCall] = {
    "nvidia": call_nvidia_text,
    "openrouter": call_openrouter_text,
}


def _get_llm_factory(
    provider: str,
) -> LLMFactory:
    normalized_provider = (
        provider.strip().lower()
    )

    try:
        return LLM_FACTORIES[
            normalized_provider
        ]
    except KeyError as error:
        supported = ", ".join(
            sorted(LLM_FACTORIES)
        )

        raise ValueError(
            "Неизвестный LLM-провайдер "
            f"{provider!r}. "
            f"Поддерживаются: {supported}."
        ) from error


def _get_text_call(
    provider: str,
) -> TextCall:
    normalized_provider = (
        provider.strip().lower()
    )

    try:
        return TEXT_CALLS[
            normalized_provider
        ]
    except KeyError as error:
        supported = ", ".join(
            sorted(TEXT_CALLS)
        )

        raise ValueError(
            "Неизвестный текстовый LLM-провайдер "
            f"{provider!r}. "
            f"Поддерживаются: {supported}."
        ) from error


# LlamaIndex-агенты
get_orchestrator_llm = _get_llm_factory(
    LLM_ORCHESTRATOR_PROVIDER
)

get_specialized_llm = _get_llm_factory(
    LLM_SPECIALIZED_AGENT_PROVIDER
)

get_adaptation_service_llm = _get_llm_factory(
    LLM_ADAPTATION_PROVIDER
)

get_statistics_sql_llm = _get_llm_factory(
    LLM_STATISTICS_SQL_PROVIDER
)

get_statistics_answer_llm = _get_llm_factory(
    LLM_STATISTICS_ANSWER_PROVIDER
)

get_structured_data_llm = _get_llm_factory(
    LLM_STRUCTURED_DATA_PROVIDER
)

# Обычные текстовые вызовы
call_dialog_service_text = _get_text_call(
    LLM_DIALOG_PROVIDER
)

call_npa_service_text = _get_text_call(
    LLM_NPA_PROVIDER
)

call_method_docs_service_text = _get_text_call(
    LLM_METHOD_DOCS_PROVIDER
)

call_internet_resources_service_text = (
    _get_text_call(
        LLM_INTERNET_RESOURCES_PROVIDER
    )
)
