from llama_index.core.agent.workflow import FunctionAgent

from core.config import (
    LLM_SPECIALIZED_AGENT_MODEL,
    AGENT_MAX_TOKENS,
    AGENT_TEMPERATURE
)

from infrastructure.llm.providers.provider_registry import (
    get_specialized_llm
)

from agents.tools import (
    adaptation_answer_tool,
    dialog_answer_tool,
    internet_resources_answer_tool,
    method_docs_answer_tool,
    npa_answer_tool,
    statistics_answer_tool,
)

# Пока все специализированные агенты используют один и тот же LLM.
# Отдельная переменная оставлена, чтобы сохранить текущую логику проекта
# и возможность позже назначить специализированным агентам другую модель.
sub_agent_llm = get_specialized_llm(
    model=LLM_SPECIALIZED_AGENT_MODEL,
    temperature=AGENT_TEMPERATURE,
    max_tokens=AGENT_MAX_TOKENS,
    function_calling=True,
)

adaptation_agent = FunctionAgent(
    system_prompt=(
        "Ты агент по адаптационным мероприятиям. "
        "Для ответа обязательно вызови инструмент "
        "adaptation_answer_tool и верни пользователю его "
        "содержательный результат без технических пояснений."
    ),
    llm=sub_agent_llm,
    tools=[adaptation_answer_tool],
)


npa_agent = FunctionAgent(
    system_prompt=(
        "Ты агент по нормативно-правовым актам. "
        "Для ответа обязательно вызови инструмент "
        "npa_answer_tool и верни пользователю его "
        "содержательный результат без технических пояснений."
    ),
    llm=sub_agent_llm,
    tools=[npa_answer_tool],
)

method_docs_agent = FunctionAgent(
    system_prompt=(
        "Ты агент по методическим рекомендациям и аналитическим "
        "документам. Для ответа обязательно вызови инструмент "
        "method_docs_answer_tool и верни пользователю его "
        "содержательный результат без технических пояснений."
    ),
    llm=sub_agent_llm,
    tools=[method_docs_answer_tool],
)


statistics_agent = FunctionAgent(
    system_prompt=(
        "Ты статистический агент. Для ответа обязательно вызови "
        "инструмент statistics_answer_tool. "
        "Не составляй SQL самостоятельно внутри этого агента, "
        "это делает инструмент."
    ),
    llm=sub_agent_llm,
    tools=[statistics_answer_tool],
)


internet_resources_agent = FunctionAgent(
    system_prompt=(
        "Ты агент по интернет-ресурсам и внешним источникам. "
        "Для ответа обязательно вызови инструмент "
        "internet_resources_answer_tool и верни его результат."
    ),
    llm=sub_agent_llm,
    tools=[internet_resources_answer_tool],
)


dialog_agent = FunctionAgent(
    system_prompt=(
        "Ты диалоговый агент для общих консультационных вопросов. "
        "Для ответа обязательно вызови инструмент "
        "dialog_answer_tool и верни его результат."
    ),
    llm=sub_agent_llm,
    tools=[dialog_answer_tool],
)
