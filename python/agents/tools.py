import asyncio
from collections.abc import Callable
from typing import Any

from services.adaptation_service import generate_adaptation_response
from services.dialog_service import generate_dialog_response
from services.internet_resources_service import (
    generate_internet_resources_response,
)
from services.method_docs_service import (
    generate_method_docs_response,
)
from services.npa_service import generate_npa_response
from services.statistics_service import generate_statistics_response

async def _to_thread(func, *args, **kwargs):
    return await asyncio.to_thread(func, *args, **kwargs)
async def adaptation_answer_tool(query: str, conversation_history: str = "") -> str:
    """Получить рекомендации по адаптационным мероприятиям из базы знаний."""
    return await _to_thread(generate_adaptation_response, query, conversation_history or None)


async def npa_answer_tool(query: str, conversation_history: str = "") -> str:
    """Получить ответ по нормативно-правовым актам, ГОСТам, СП, приказам и постановлениям."""
    return await _to_thread(generate_npa_response, query, conversation_history or None)


async def method_docs_answer_tool(query: str, conversation_history: str = "") -> str:
    """Получить ответ по методическим рекомендациям, аналитическим документам, докладам и материалам семинаров."""
    return await _to_thread(generate_method_docs_response, query, conversation_history or None)


async def statistics_answer_tool(query: str, conversation_history: str = "") -> str:
    """Получить статистические данные из PostgreSQL по естественно-языковому запросу."""
    return await _to_thread(generate_statistics_response, query, conversation_history or None)


async def internet_resources_answer_tool(query: str, conversation_history: str = "") -> str:
    """Подобрать и объяснить интернет-ресурсы или найти актуальную информацию во внешних источниках."""
    return await _to_thread(generate_internet_resources_response, query, conversation_history or None)


async def dialog_answer_tool(query: str, conversation_history: str = "") -> str:
    """Дать общий консультационный ответ по климатическим рискам и адаптации."""
    return await _to_thread(generate_dialog_response, query, conversation_history or None)
