import logging

from fastapi import APIRouter, HTTPException

from agents.orchestrator import process_query_multiagent
from schemas.question import (
    QuestionRequest,
    QuestionResponse,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["questions"],
)


@router.post(
    "/ask",
    response_model=QuestionResponse,
)
async def ask_question_simple(
    request: QuestionRequest,
) -> QuestionResponse:
    try:
        answer = await process_query_multiagent(
            request.question,
            context_history=request.context,
        )

        return QuestionResponse(
            answer=str(answer),
            status="success",
        )

    except Exception as exc:
        logger.exception(
            "Ошибка обработки запроса /ask"
        )
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc
