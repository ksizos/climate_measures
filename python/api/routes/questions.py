import asyncio
import logging

from fastapi import APIRouter, HTTPException

from agents.orchestrator import (
    process_query_multiagent,
)
from schemas.question import (
    QuestionRequest,
    QuestionResponse,
)


logger = logging.getLogger(__name__)


router = APIRouter(
    tags=["questions"],
)


active_requests: dict[
    str,
    asyncio.Task,
] = {}


@router.post(
    "/ask",
    response_model=QuestionResponse,
)
async def ask_question_simple(
    request: QuestionRequest,
) -> QuestionResponse:

    request_id = request.request_id

    task: asyncio.Task | None = None

    try:

        task = asyncio.create_task(
            process_query_multiagent(
                request.question,
                context_history=request.context,
            ),
            name=(
                f"climate-request-"
                f"{request_id or 'anonymous'}"
            ),
        )


        if request_id:

            active_requests[
                request_id
            ] = task

            logger.info(
                "▶ Запущена генерация: "
                "request_id=%s",
                request_id,
            )


        answer = await task


        return QuestionResponse(
            answer=str(answer),
            status="success",
        )


    except asyncio.CancelledError:

        logger.info(
            "⛔ Генерация отменена: "
            "request_id=%s",
            request_id,
        )

        raise HTTPException(
            status_code=499,
            detail="Generation cancelled",
        )


    except Exception as exc:

        logger.exception(
            "Ошибка /ask: "
            "request_id=%s",
            request_id,
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


    finally:

        if (
            request_id
            and
            active_requests.get(
                request_id
            ) is task
        ):
            active_requests.pop(
                request_id,
                None,
            )


@router.post(
    "/cancel/{request_id}",
)
async def cancel_question(
    request_id: str,
) -> dict:

    logger.info(
        "Получен STOP: request_id=%s",
        request_id,
    )


    task = active_requests.get(
        request_id
    )


    if task is None:

        logger.warning(
            "STOP: задача не найдена: "
            "request_id=%s. "
            "Активные request_id=%s",
            request_id,
            list(active_requests.keys()),
        )

        return {
            "success": True,
            "cancelled": False,
        }


    if task.done():

        active_requests.pop(
            request_id,
            None,
        )

        return {
            "success": True,
            "cancelled": False,
        }


    logger.info(
        "Отменяем asyncio task: %s",
        request_id,
    )


    task.cancel()


    try:

        await task

    except asyncio.CancelledError:
        pass

    except HTTPException:
        pass

    except Exception as exc:

        logger.debug(
            "Задача завершилась во время STOP: "
            "request_id=%s error=%s",
            request_id,
            exc,
        )


    active_requests.pop(
        request_id,
        None,
    )


    logger.info(
        "✓ Asyncio task остановлен: %s",
        request_id,
    )


    return {
        "success": True,
        "cancelled": True,
    }
