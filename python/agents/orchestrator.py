from __future__ import annotations

import asyncio
import json
import logging

from agents.registry import (
    AVAILABLE_AGENTS,
    run_agent,
)
from core.config import (
    AGGREGATOR_MAX_TOKENS,
    ORCHESTRATOR_MAX_TOKENS,
)
from infrastructure.llm.provider import (
    achat_text,
)
from prompts.aggregation import (
    AGGREGATION_SYSTEM_PROMPT,
)
from prompts.orchestrator import (
    ORCHESTRATOR_SYSTEM_PROMPT,
)


logger = logging.getLogger(__name__)


def _extract_json_object(text: str) -> dict:
    """
    Извлекает JSON даже если модель завернула его
    в ```json ... ```.
    """

    cleaned = (
        text
        .replace("```json", "")
        .replace("```JSON", "")
        .replace("```", "")
        .strip()
    )

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "Оркестратор не вернул JSON."
        )

    return json.loads(
        cleaned[start:end + 1]
    )


def _validate_selected_agents(
    agents: list[str],
) -> list[str]:
    """
    Оставляет только существующих агентов
    и удаляет дубликаты.
    """

    result: list[str] = []

    for agent_name in agents:
        normalized = str(
            agent_name
        ).strip().lower()

        if normalized not in AVAILABLE_AGENTS:
            continue

        if normalized not in result:
            result.append(normalized)

    # dialog используется только самостоятельно.
    if (
        "dialog" in result
        and len(result) > 1
    ):
        result.remove("dialog")

    return result


async def select_agents(
    user_question: str,
    conversation_history: str = "",
) -> list[str]:
    """
    Единственная задача оркестратора —
    выбрать имена агентов.

    Он НЕ запускает их сам.
    """

    user_prompt = f"""
История диалога:
{conversation_history or "нет"}

Текущий запрос пользователя:
{user_question}

Выбери необходимые специализированные агенты.

Верни СТРОГО JSON следующего вида:

{{
  "agents": ["adaptation", "statistics"]
}}

Допустимые значения:
{", ".join(AVAILABLE_AGENTS)}
""".strip()

    raw_response = await achat_text(
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.0,
        max_new_tokens=ORCHESTRATOR_MAX_TOKENS,
    )

    try:
        data = _extract_json_object(
            raw_response
        )

        selected = _validate_selected_agents(
            data.get("agents", [])
        )

        if selected:
            return selected

    except Exception:
        logger.exception(
            "Не удалось разобрать ответ оркестратора: %s",
            raw_response,
        )

    # Безопасный fallback.
    return ["dialog"]


async def _run_agent_safely(
    agent_name: str,
    user_question: str,
    conversation_history: str,
) -> tuple[str, str]:
    try:
        result = await run_agent(
            agent_name,
            user_question,
            conversation_history or None,
        )

        return agent_name, result

    except asyncio.CancelledError:
        raise

    except Exception as error:
        logger.exception(
            "Ошибка агента %s",
            agent_name,
        )

        return (
            agent_name,
            (
                "Не удалось получить результат "
                f"от направления {agent_name}: {error}"
            ),
        )


async def aggregate_agent_answers(
    *,
    user_question: str,
    agent_results: dict[str, str],
) -> str:
    """
    Агрегируется ТОЛЬКО когда результатов > 1.
    """

    blocks = []

    for agent_name, answer in agent_results.items():
        blocks.append(
            f"""
=== {agent_name} ===
{answer}
""".strip()
        )

    user_prompt = f"""
Исходный запрос пользователя:
{user_question}

Независимые экспертные ответы:

{chr(10).join(blocks)}

Сформируй единый итоговый ответ.
""".strip()

    return await achat_text(
        system_prompt=AGGREGATION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.1,
        max_new_tokens=AGGREGATOR_MAX_TOKENS,
    )


async def process_query_multiagent(
    user_question: str,
    context_history: str | None = None,
) -> str:
    normalized_question = (
        user_question.strip()
    )

    if not normalized_question:
        return (
            "Ошибка: пожалуйста, введите ваш запрос."
        )

    normalized_history = (
        context_history.strip()
        if context_history
        else ""
    )

    selected_agents = await select_agents(
        normalized_question,
        normalized_history,
    )

    logger.info(
        "Оркестратор выбрал агентов: %s",
        selected_agents,
    )

    # КЛЮЧЕВОЕ МЕСТО:
    # все выбранные агенты запускаются одновременно.
    tasks = [
        asyncio.create_task(
            _run_agent_safely(
                agent_name,
                normalized_question,
                normalized_history,
            ),
            name=f"agent:{agent_name}",
        )
        for agent_name in selected_agents
    ]

    try:
        completed = await asyncio.gather(
            *tasks
        )

    except asyncio.CancelledError:
        for task in tasks:
            task.cancel()

        await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

        raise

    agent_results = {
        agent_name: result
        for agent_name, result in completed
    }

    # Согласно требованию:
    # один агент -> никакого aggregation LLM.
    if len(agent_results) == 1:
        return next(
            iter(agent_results.values())
        )

    return await aggregate_agent_answers(
        user_question=normalized_question,
        agent_results=agent_results,
    )