from __future__ import annotations

from functools import lru_cache

from llama_index.llms.openrouter import OpenRouter
from openai import OpenAI

from core.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MAX_RETRIES,
    OPENROUTER_REQUEST_TIMEOUT,
)


if not OPENROUTER_API_KEY:
    raise RuntimeError(
        "Не задан OPENROUTER_API_KEY."
    )


client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL,
    timeout=OPENROUTER_REQUEST_TIMEOUT,
    max_retries=OPENROUTER_MAX_RETRIES,
)


@lru_cache(maxsize=32)
def get_openrouter_llm(
    model: str,
    *,
    temperature: float = 0.2,
    max_tokens: int = 2000,
    function_calling: bool = False,
) -> OpenRouter:
    if not model or not model.strip():
        raise ValueError(
            "Не указана модель OpenRouter."
        )

    return OpenRouter(
        api_key=OPENROUTER_API_KEY,
        model=model.strip(),
        temperature=temperature,
        max_tokens=max_tokens,
        context_window=400_000,
        is_chat_model=True,
        is_function_calling_model=(
            function_calling
        ),
        timeout=OPENROUTER_REQUEST_TIMEOUT,
        max_retries=OPENROUTER_MAX_RETRIES,
    )


def call_openrouter_text(
    *,
    model: str,
    user_prompt: str,
    system_prompt: str | None = None,
    temperature: float = 0.2,
    max_output_tokens: int = 2000,
) -> str:
    messages: list[dict[str, str]] = []

    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt,
        })

    messages.append({
        "role": "user",
        "content": user_prompt,
    })

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_output_tokens,
        stream=False,
        extra_body={
            "provider": {
                "allow_fallbacks": True,
                "sort": "latency",
            }
        },
    )

    if not response.choices:
        raise RuntimeError(
            "OpenRouter вернул ответ без choices."
        )

    return (
        response.choices[0].message.content
        or ""
    ).strip()
