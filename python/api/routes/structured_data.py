import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException
from llama_index.core.llms import ChatMessage

from core.config import (
    LLM_STRUCTURED_DATA_MODEL,
    AGENT_MAX_TOKENS,
)
from infrastructure.llm.providers.provider_registry import (
    get_structured_data_llm,
)
from prompts.structured_data import (
    STRUCTURED_DATA_SYSTEM_PROMPT,
)
from schemas.structured_data import StructuredDataRequest

logger = logging.getLogger(__name__)

router = APIRouter()


structured_data_llm = get_structured_data_llm(
    model=LLM_STRUCTURED_DATA_MODEL,
    temperature=0.1,
    max_tokens=AGENT_MAX_TOKENS,
    function_calling=False,
)


@router.post("/generate-structured-data")
async def generate_structured_data(
    request: StructuredDataRequest,
) -> dict:
    messages = [
        ChatMessage(
            role="system",
            content=STRUCTURED_DATA_SYSTEM_PROMPT,
        ),
        ChatMessage(
            role="user",
            content=request.prompt,
        ),
    ]

    try:
        response = await asyncio.to_thread(
            structured_data_llm.chat,
            messages,
        )

        text = (
            response.message.content
            or ""
        ).strip()

        if not text:
            raise RuntimeError(
                "Модель не вернула текст."
            )

        cleaned_text = (
            text
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        data = json.loads(
            cleaned_text
        )

        return {
            "success": True,
            "data": data,
        }

    except json.JSONDecodeError as error:
        logger.exception(
            "Модель вернула некорректный JSON"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Модель вернула некорректный JSON."
            ),
        ) from error

    except Exception as error:
        logger.exception(
            "Ошибка генерации структурированных данных"
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error
