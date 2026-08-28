from __future__ import annotations

import logging

from functools import lru_cache
from importlib import import_module
from types import ModuleType

from core.config import LLM_PROVIDER


logger = logging.getLogger(__name__)


_BACKENDS = {
    "local": (
        "infrastructure.llm.local_yandex"
    ),
    "yandex_api": (
        "infrastructure.llm.yandex_api"
    ),
}


@lru_cache(maxsize=1)
def _get_backend() -> ModuleType:
    """
    Загружает выбранную реализацию LLM.

    Возможные значения:
    - local
    - yandex_api
    """

    provider = LLM_PROVIDER.strip().lower()

    module_name = _BACKENDS.get(
        provider
    )

    if module_name is None:
        raise ValueError(
            "Неизвестный LLM_PROVIDER: "
            f"{LLM_PROVIDER!r}. "
            "Допустимые значения: "
            + ", ".join(_BACKENDS.keys())
        )

    logger.info(
        "LLM provider: %s",
        provider,
    )

    return import_module(
        module_name
    )


def chat_text(
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_new_tokens: int = 512,
) -> str:
    """
    Синхронная генерация текста
    через выбранный LLM backend.
    """

    backend = _get_backend()

    return backend.chat_text(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=temperature,
        max_new_tokens=max_new_tokens,
    )


async def achat_text(
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_new_tokens: int = 512,
) -> str:
    """
    Асинхронная генерация текста
    через выбранный LLM backend.
    """

    backend = _get_backend()

    return await backend.achat_text(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=temperature,
        max_new_tokens=max_new_tokens,
    )


def preload_llm() -> None:
    """
    Предварительная инициализация
    выбранного LLM backend.
    """

    backend = _get_backend()

    backend.preload_llm()