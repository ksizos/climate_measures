from __future__ import annotations

import json
import logging

from fastapi import (
    APIRouter,
    HTTPException,
)

from infrastructure.llm.local_yandex import (
    achat_text,
)

from prompts.structured_data import (
    STRUCTURED_DATA_SYSTEM_PROMPT,
)

from schemas.structured_data import (
    StructuredDataRequest,
)


logger = logging.getLogger(__name__)

router = APIRouter()


def _extract_json_text(
    text: str,
) -> str:
    """
    Убирает markdown code fence,
    если модель его добавила.
    """

    cleaned = (
        text
        .replace("```json", "")
        .replace("```JSON", "")
        .replace("```", "")
        .strip()
    )

    return cleaned


@router.post(
    "/generate-structured-data"
)
async def generate_structured_data(
    request: StructuredDataRequest,
) -> dict:

    try:
        text = await achat_text(
            system_prompt=(
                STRUCTURED_DATA_SYSTEM_PROMPT
            ),
            user_prompt=request.prompt,
            temperature=0.0,
            max_new_tokens=1500,
        )

        text = text.strip()

        if not text:
            raise RuntimeError(
                "Модель не вернула текст."
            )

        cleaned_text = _extract_json_text(
            text
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
            "Ошибка генерации "
            "структурированных данных"
        )

        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error