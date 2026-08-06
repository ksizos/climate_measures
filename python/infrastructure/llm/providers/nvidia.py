from __future__ import annotations

import logging
import time
from functools import lru_cache
from typing import Any

from llama_index.llms.openai_like import OpenAILike
from openai import (
    APIStatusError,
    OpenAI,
)

from core.config import (
    NVIDIA_API_KEY,
    NVIDIA_BASE_URL,
    NVIDIA_MAX_RETRIES,
    NVIDIA_REQUEST_TIMEOUT,
)

logger = logging.getLogger(__name__)

def normalize_nvidia_base_url(
    value: str,
) -> str:
    """
    Нормализует базовый URL NVIDIA API.

    Допустимый итог:
    https://integrate.api.nvidia.com/v1
    """

    if not value or not value.strip():
        raise RuntimeError(
            "Переменная NVIDIA_BASE_URL не задана."
        )

    base_url = value.strip().rstrip("/")

    if base_url.endswith("/chat/completions"):
        base_url = base_url.removesuffix(
            "/chat/completions"
        )

    if not base_url.endswith("/v1"):
        base_url = f"{base_url}/v1"

    return base_url


if not NVIDIA_API_KEY:
    raise RuntimeError(
        "Переменная NVIDIA_API_KEY не задана."
    )

NORMALIZED_NVIDIA_BASE_URL = (
    normalize_nvidia_base_url(
        NVIDIA_BASE_URL
    )
)

REQUEST_TIMEOUT = float(
    NVIDIA_REQUEST_TIMEOUT
)

MAX_RETRIES = int(
    NVIDIA_MAX_RETRIES
)


# Один обычный OpenAI-compatible клиент.
# Модель передаётся отдельно в каждом запросе.
client = OpenAI(
    api_key=NVIDIA_API_KEY,
    base_url=NORMALIZED_NVIDIA_BASE_URL,
    timeout=REQUEST_TIMEOUT,

    # Повторные попытки контролируем сами.
    max_retries=0,
)


@lru_cache(maxsize=32)
def get_nvidia_llm(
    model: str,
    *,
    temperature: float = 0.2,
    max_tokens: int = 2000,
    function_calling: bool = True,
) -> OpenAILike:
    """
    Возвращает LlamaIndex-совместимый объект модели NVIDIA.

    Объекты кэшируются. Если несколько компонентов используют
    одну модель и одинаковые параметры, новый объект не создаётся.

    Args:
        model:
            Точное имя модели NVIDIA.

        temperature:
            Температура по умолчанию.

        max_tokens:
            Максимальная длина ответа.

        function_calling:
            Поддерживает ли модель tool/function calling.
            Для FunctionAgent должно быть True.
    """

    normalized_model = model.strip()

    if not normalized_model:
        raise ValueError(
            "Имя модели NVIDIA не может быть пустым."
        )

    logger.info(
        "Создание NVIDIA LlamaIndex LLM: "
        "model=%s, function_calling=%s",
        normalized_model,
        function_calling,
    )

    return OpenAILike(
        model=normalized_model,
        api_key=NVIDIA_API_KEY,
        api_base=NORMALIZED_NVIDIA_BASE_URL,

        is_chat_model=True,
        is_function_calling_model=(
            function_calling
        ),

        temperature=temperature,
        max_tokens=max_tokens,

        timeout=REQUEST_TIMEOUT,
        max_retries=MAX_RETRIES,
    )


def call_nvidia_text(
    messages: list[dict[str, Any]] | None = None,
    user_prompt: str | None = None,
    system_prompt: str | None = None,
    *,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 2000,
    max_output_tokens: int | None = None,
    extra_body: dict[str, Any] | None = None,
) -> str:
    """
    Выполняет обычный синхронный запрос к NVIDIA.

    Модель можно передать через параметр model.

    Поддерживаются старые способы вызова:
    - messages=[...];
    - user_prompt + system_prompt;
    - max_output_tokens.
    """

    selected_model = (
        model.strip()
    )

    if max_output_tokens is not None:
        max_tokens = max_output_tokens

    prepared_messages: list[
        dict[str, Any]
    ] = []

    if messages is not None:
        prepared_messages.extend(messages)

    else:
        if system_prompt:
            prepared_messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        if user_prompt:
            prepared_messages.append(
                {
                    "role": "user",
                    "content": user_prompt,
                }
            )

    if not prepared_messages:
        raise ValueError(
            "Необходимо передать messages "
            "или user_prompt."
        )

    request_kwargs: dict[str, Any] = {
        "model": selected_model,
        "messages": prepared_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    if extra_body:
        request_kwargs["extra_body"] = (
            extra_body
        )

    total_attempts = MAX_RETRIES + 1
    last_error: Exception | None = None

    for attempt in range(
        1,
        total_attempts + 1,
    ):
        logger.info(
            "NVIDIA request: model=%s, "
            "attempt=%s/%s, messages=%s",
            selected_model,
            attempt,
            total_attempts,
            len(prepared_messages),
        )

        try:
            response = (
                client
                .chat
                .completions
                .create(**request_kwargs)
            )

            if not response.choices:
                raise RuntimeError(
                    "NVIDIA вернула ответ "
                    "без choices."
                )

            message = (
                response
                .choices[0]
                .message
            )

            content = message.content

            if isinstance(content, list):
                content = "".join(
                    str(
                        item.get("text", "")
                    )
                    for item in content
                    if isinstance(item, dict)
                )

            if not content:
                content = getattr(
                    message,
                    "reasoning_content",
                    None,
                )

            if not content:
                raise RuntimeError(
                    "NVIDIA вернула пустой ответ."
                )

            return str(content).strip()

        except APIStatusError as exc:
            last_error = exc

            logger.warning(
                "Ошибка NVIDIA API: "
                "model=%s, status=%s, error=%s",
                selected_model,
                exc.status_code,
                exc,
            )

            # Повторяем только серверные ошибки.
            if (
                exc.status_code < 500
                or attempt == total_attempts
            ):
                raise

            time.sleep(2)

    raise RuntimeError(
        "Не удалось получить ответ NVIDIA "
        f"от модели '{selected_model}'."
    ) from last_error
