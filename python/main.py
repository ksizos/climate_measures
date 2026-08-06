from __future__ import annotations

import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import (
    admin,
    exports,
    health,
    measures,
    questions,
    structured_data,
)
from core.config import APP_TITLE
from core.logging_config import setup_logging


setup_logging()

logger = logging.getLogger(__name__)


def get_cors_origins() -> list[str]:
    """
    Возвращает список разрешённых CORS-origin
    из переменной окружения CORS_ALLOW_ORIGINS.
    """

    raw_origins = os.getenv(
        "CORS_ALLOW_ORIGINS",
        (
            "http://localhost:8000,"
            "http://127.0.0.1:8000"
        ),
    )

    return [
        origin.strip()
        for origin in raw_origins.split(",")
        if origin.strip()
    ]


def create_app() -> FastAPI:
    """
    Создаёт и настраивает FastAPI-приложение.
    """

    application = FastAPI(
        title=APP_TITLE,
        version="1.0.0",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health.router)
    application.include_router(questions.router)
    application.include_router(measures.router)
    application.include_router(exports.router)
    application.include_router(
        structured_data.router
    )
    application.include_router(admin.router)

    @application.on_event("startup")
    async def startup_event() -> None:
        logger.info(
            "Приложение %s запущено",
            APP_TITLE,
        )

    @application.on_event("shutdown")
    async def shutdown_event() -> None:
        logger.info(
            "Приложение %s остановлено",
            APP_TITLE,
        )

    return application


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(
            os.getenv(
                "APP_PORT",
                "8001",
            )
        ),
        reload=False,
    )
