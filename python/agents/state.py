from typing import Any

from llama_index.core.workflow import Context


async def _save_agent_result(
    ctx: Context,
    agent_name: str,
    result: Any,
) -> None:
    """
    Сохраняет результат агента в состоянии текущего workflow.

    В AgentWorkflow пользовательское состояние находится
    внутри ключа "state".
    """

    result_text = str(result).strip()

    async with ctx.store.edit_state() as store_state:
        workflow_state = store_state["state"]

        try:
            used_agents = list(workflow_state["used_agents"])
        except (KeyError, TypeError):
            used_agents = []

        try:
            agent_outputs = dict(workflow_state["agent_outputs"])
        except (KeyError, TypeError):
            agent_outputs = {}

        if agent_name not in used_agents:
            used_agents.append(agent_name)

        agent_outputs[agent_name] = result_text

        workflow_state["used_agents"] = used_agents
        workflow_state["agent_outputs"] = agent_outputs


async def _get_previous_agent_outputs(
    ctx: Context,
    max_chars: int = 6000,
) -> str:
    """
    Возвращает результаты агентов, которые уже были вызваны
    в рамках текущего workflow.
    """

    try:
        store_state = await ctx.store.get_state()
        workflow_state = store_state["state"]
        agent_outputs = workflow_state["agent_outputs"]
    except (KeyError, TypeError, AttributeError):
        return ""

    if not isinstance(agent_outputs, dict):
        return ""

    parts: list[str] = []

    for agent_name, result in agent_outputs.items():
        result_text = str(result).strip()

        if not result_text:
            continue

        parts.append(
            f"Результат агента {agent_name}:\n"
            f"{result_text}"
        )

    combined = "\n\n".join(parts)

    if len(combined) > max_chars:
        combined = combined[:max_chars].rstrip()
        combined += "\n\n[Предыдущие результаты сокращены]"

    return combined


async def get_used_agents(ctx: Context) -> list[str]:
    """
    Возвращает список агентов, использованных workflow.
    """

    try:
        store_state = await ctx.store.get_state()
        workflow_state = store_state["state"]
        used_agents = workflow_state["used_agents"]
    except (KeyError, TypeError, AttributeError):
        return []

    if not isinstance(used_agents, list):
        return []

    return [str(agent_name) for agent_name in used_agents]
