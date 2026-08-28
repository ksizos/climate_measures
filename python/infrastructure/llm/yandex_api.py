from __future__ import annotations

from functools import lru_cache

from openai import AsyncOpenAI, OpenAI

from core.config import (
    YANDEX_CLOUD_API_KEY,
    YANDEX_CLOUD_BASE_URL,
    YANDEX_CLOUD_FOLDER,
    YANDEX_CLOUD_MODEL,
)


def _validate_config() -> None:
    """
    Проверяет обязательные настройки
    Yandex Cloud API.
    """

    missing: list[str] = []

    if not YANDEX_CLOUD_FOLDER:
        missing.append(
            "YANDEX_CLOUD_FOLDER"
        )

    if not YANDEX_CLOUD_API_KEY:
        missing.append(
            "YANDEX_CLOUD_API_KEY"
        )

    if not YANDEX_CLOUD_MODEL:
        missing.append(
            "YANDEX_CLOUD_MODEL"
        )

    if missing:
        raise RuntimeError(
            "Не заданы настройки Yandex Cloud API: "
            + ", ".join(missing)
        )


def _model_uri() -> str:
    """
    Формирует URI модели Yandex Cloud.
    """

    return (
        f"gpt://{YANDEX_CLOUD_FOLDER}/"
        f"{YANDEX_CLOUD_MODEL}"
    )


@lru_cache(maxsize=1)
def _get_client() -> OpenAI:
    """
    Синхронный OpenAI-compatible клиент.
    """

    _validate_config()

    return OpenAI(
        api_key=YANDEX_CLOUD_API_KEY,
        base_url=YANDEX_CLOUD_BASE_URL,
        project=YANDEX_CLOUD_FOLDER,
        timeout=120.0,
        max_retries=2,
    )


@lru_cache(maxsize=1)
def _get_async_client() -> AsyncOpenAI:
    """
    Асинхронный OpenAI-compatible клиент.
    """

    _validate_config()

    return AsyncOpenAI(
        api_key=YANDEX_CLOUD_API_KEY,
        base_url=YANDEX_CLOUD_BASE_URL,
        project=YANDEX_CLOUD_FOLDER,
        timeout=120.0,
        max_retries=2,
    )


def chat_text(
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_new_tokens: int = 512,
) -> str:
    """
    Синхронный вызов YandexGPT через API.

    Интерфейс специально совпадает
    с local_yandex.chat_text().
    """

    client = _get_client()

    response = client.responses.create(
        model=_model_uri(),
        temperature=temperature,
        instructions=system_prompt,
        input=user_prompt,
        max_output_tokens=max_new_tokens,
    )

    return (
        response.output_text
        or ""
    ).strip()


async def achat_text(
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_new_tokens: int = 512,
) -> str:
    """
    Асинхронный вызов YandexGPT через API.

    Интерфейс совпадает
    с local_yandex.achat_text().
    """

    client = _get_async_client()

    response = await client.responses.create(
        model=_model_uri(),
        temperature=temperature,
        instructions=system_prompt,
        input=user_prompt,
        max_output_tokens=max_new_tokens,
    )

    return (
        response.output_text
        or ""
    ).strip()


def preload_llm() -> None:
    """
    Для API ничего загружать в RAM не требуется.

    Просто заранее проверяем конфигурацию
    и создаём клиент.
    """

    _validate_config()

    _get_client()