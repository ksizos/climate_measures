from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.workflow import Context

from agents.specialized import (
    adaptation_agent,
    dialog_agent,
    internet_resources_agent,
    method_docs_agent,
    npa_agent,
    statistics_agent,
)

from prompts.orchestrator import ORCHESTRATOR_SYSTEM_PROMPT

from agents.state import (
    _get_previous_agent_outputs,
    _save_agent_result,
)

from core.config import (
    LLM_ORCHESTRATOR_MODEL,
    ORCHESTRATOR_TEMPERATURE,
    ORCHESTRATOR_MAX_TOKENS
)
from infrastructure.llm.providers.provider_registry import (
    get_orchestrator_llm
)

# Пока сохраняем текущую логику:
# специализированные агенты и оркестратор используют один LLM-клиент.
orchestrator_llm = get_orchestrator_llm(
    model=LLM_ORCHESTRATOR_MODEL,
    temperature=ORCHESTRATOR_TEMPERATURE,
    max_tokens=ORCHESTRATOR_MAX_TOKENS,
    function_calling=True,
)

async def _build_agent_user_message(
    ctx: Context,
    prompt: str,
    conversation_history: str = "",
) -> str:
    """
    Формирует сообщение для специализированного агента.

    В сообщение включаются:
    - текущая задача;
    - история диалога;
    - результаты агентов, уже вызванных оркестратором.
    """
    previous_outputs = await _get_previous_agent_outputs(ctx)

    parts = [
        f"Текущий запрос пользователя:\n{prompt.strip()}"
    ]

    if conversation_history and conversation_history.strip():
        parts.append(
            f"История диалога:\n{conversation_history.strip()}"
        )

    if previous_outputs:
        parts.append(
            "Результаты других агентов, вызванных ранее "
            "в рамках этого же запроса:\n"
            f"{previous_outputs}"
        )

    parts.append(
        "Используй результаты других агентов только в том случае, "
        "если они релевантны текущей задаче. "
        "Не повторяй их дословно."
    )

    return "\n\n".join(parts)


async def call_adaptation_agent(
    ctx: Context,
    prompt: str,
    conversation_history: str = "",
) -> str:
    """Запускает агента по адаптационным мероприятиям."""
    user_msg = await _build_agent_user_message(
        ctx=ctx,
        prompt=prompt,
        conversation_history=conversation_history,
    )

    result = await adaptation_agent.run(user_msg=user_msg)
    text = str(result)

    await _save_agent_result(ctx, "adaptation_agent", text)
    return text


async def call_npa_agent(
    ctx: Context,
    prompt: str,
    conversation_history: str = "",
) -> str:
    """Запускает агента по нормативно-правовым актам."""
    user_msg = await _build_agent_user_message(
        ctx=ctx,
        prompt=prompt,
        conversation_history=conversation_history,
    )

    result = await npa_agent.run(user_msg=user_msg)
    text = str(result)

    await _save_agent_result(ctx, "npa_agent", text)
    return text


async def call_method_docs_agent(
    ctx: Context,
    prompt: str,
    conversation_history: str = "",
) -> str:
    """Запускает агента по методическим и аналитическим документам."""
    user_msg = await _build_agent_user_message(
        ctx=ctx,
        prompt=prompt,
        conversation_history=conversation_history,
    )

    result = await method_docs_agent.run(user_msg=user_msg)
    text = str(result)

    await _save_agent_result(ctx, "method_docs_agent", text)
    return text


async def call_statistics_agent(
    ctx: Context,
    prompt: str,
    conversation_history: str = "",
) -> str:
    """Запускает статистического агента."""
    user_msg = await _build_agent_user_message(
        ctx=ctx,
        prompt=prompt,
        conversation_history=conversation_history,
    )

    result = await statistics_agent.run(user_msg=user_msg)
    text = str(result)

    await _save_agent_result(ctx, "statistics_agent", text)
    return text


async def call_internet_resources_agent(
    ctx: Context,
    prompt: str,
    conversation_history: str = "",
) -> str:
    """Запускает агента по интернет-ресурсам."""
    user_msg = await _build_agent_user_message(
        ctx=ctx,
        prompt=prompt,
        conversation_history=conversation_history,
    )

    result = await internet_resources_agent.run(user_msg=user_msg)
    text = str(result)

    await _save_agent_result(
        ctx,
        "internet_resources_agent",
        text,
    )
    return text


async def call_dialog_agent(
    ctx: Context,
    prompt: str,
    conversation_history: str = "",
) -> str:
    """Запускает общего диалогового агента."""
    user_msg = await _build_agent_user_message(
        ctx=ctx,
        prompt=prompt,
        conversation_history=conversation_history,
    )

    result = await dialog_agent.run(user_msg=user_msg)
    text = str(result)

    await _save_agent_result(ctx, "dialog_agent", text)
    return text


orchestrator = FunctionAgent(
    system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
    llm=orchestrator_llm,
    tools=[
        call_adaptation_agent,
        call_npa_agent,
        call_method_docs_agent,
        call_statistics_agent,
        call_internet_resources_agent,
        call_dialog_agent,
    ],
    initial_state={
        "state": {
            "used_agents": [],
            "agent_outputs": [],
        }
    },
)

async def process_query_multiagent(
    user_question: str,
    context_history: str | None = None,
) -> str:
    """
    Обрабатывает пользовательский запрос через агент-оркестратор.
    """
    normalized_question = user_question.strip()

    if not normalized_question:
        return "Ошибка: пожалуйста, введите ваш запрос."

    normalized_history = (
        context_history.strip()
        if context_history
        else ""
    )

    user_msg = f"""
История диалога:
{normalized_history}

Текущий запрос пользователя:
{normalized_question}
""".strip()

    print("\n" + "=" * 80)
    print("🧭 ЗАПУСК ОРКЕСТРАТОРА")
    print("=" * 80)
    print(user_msg)
    print("=" * 80 + "\n")

    # Для каждого пользовательского запроса создается новый Context.
    # Это необходимо, чтобы результаты агентов разных запросов
    # не смешивались.
    ctx = Context(orchestrator)

    handler = orchestrator.run(
        user_msg=user_msg,
        ctx=ctx,
    )
    result = await handler

    return str(result)
