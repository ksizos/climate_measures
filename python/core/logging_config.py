import logging
import os
import sys


DEFAULT_LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)-8s | "
    "%(name)s | "
    "%(message)s"
)

DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> None:
    """
    Настраивает базовое логирование приложения.

    Уровень логирования берется из переменной окружения
    LOG_LEVEL. По умолчанию используется INFO.
    """
    log_level_name = os.getenv(
        "LOG_LEVEL",
        "INFO",
    ).upper()

    log_level = getattr(
        logging,
        log_level_name,
        logging.INFO,
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Не добавляем обработчик повторно при повторном импорте
    # или при запуске FastAPI с reload=True.
    if root_logger.handlers:
        return

    console_handler = logging.StreamHandler(
        sys.stdout
    )
    console_handler.setLevel(log_level)

    formatter = logging.Formatter(
        fmt=DEFAULT_LOG_FORMAT,
        datefmt=DEFAULT_DATE_FORMAT,
    )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
