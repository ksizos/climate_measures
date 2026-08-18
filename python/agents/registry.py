from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable

from services.adaptation_service import (
    generate_adaptation_response,
)
from services.dialog_service import (
    generate_dialog_response,
)
from services.internet_resources_service import (
    generate_internet_resources_response,
)
from services.method_docs_service import (
    generate_method_docs_response,
)
from services.npa_service import (
    generate_npa_response,
)
from services.statistics_service import (
    generate_statistics_response,
)


AGENT_REGISTRY: dict[str, Callable] = {
    "adaptation": generate_adaptation_response,
    "npa": generate_npa_response,
    "method_docs": generate_method_docs_response,
    "statistics": generate_statistics_response,
    "internet_resources": generate_internet_resources_response,
    "dialog": generate_dialog_response,
}


AVAILABLE_AGENTS = tuple(
    AGENT_REGISTRY.keys()
)


async def run_agent(
    agent_name: str,
    user_question: str,
    conversation_history: str | None = None,
) -> str:
    """
    Запускает выбранный сервис.

    Async-сервисы выполняются непосредственно.
    Sync-сервисы отправляются в отдельный thread,
    чтобы не блокировать asyncio event loop.
    """

    runner = AGENT_REGISTRY.get(agent_name)

    if runner is None:
        raise ValueError(
            f"Неизвестный агент: {agent_name}"
        )

    if inspect.iscoroutinefunction(runner):
        return await runner(
            user_question,
            conversation_history,
        )

    return await asyncio.to_thread(
        runner,
        user_question,
        conversation_history,
    )