import logging

import pandas as pd
from llama_index.core.llms import ChatMessage

from core.config import (
    LLM_STATISTICS_ANSWER_MODEL,
    LLM_STATISTICS_SQL_MODEL,
)
from infrastructure.llm.providers.provider_registry import (
    get_statistics_sql_llm, get_statistics_answer_llm
)

from infrastructure.database.sql_security import (
    extract_sql_from_llm_response,
    validate_statistics_sql,
)

from prompts.statistics import (
    STATISTICS_ANSWER_SYSTEM_PROMPT,
    STATISTICS_SCHEMA_DESCRIPTION,
    STATISTICS_SQL_SYSTEM_PROMPT,
)

from infrastructure.database.statistics_repository import (
    execute_statistics_sql,
    get_statistics_metadata,
)

from services.statistics_cache import (
    statistics_cache_key,
)
from services.statistics_matching import (
    get_top_similar_indicators,
)

import re

logger = logging.getLogger(__name__)

statistics_sql_llm = get_statistics_sql_llm(
    model=LLM_STATISTICS_SQL_MODEL,
    temperature=0.0,
    max_tokens=700,
    function_calling=False,
)

statistics_answer_llm = get_statistics_answer_llm(
    model=LLM_STATISTICS_ANSWER_MODEL,
    temperature=0.1,
    max_tokens=1000,
    function_calling=False,
)

def extract_requested_years(
    user_question: str,
) -> list[str]:
    return sorted(
        set(
            re.findall(
                r"\b(?:19|20)\d{2}\b",
                user_question,
            )
        )
    )


def format_statistics_context(
    user_question: str,
) -> str:
    metadata = get_statistics_metadata(
        statistics_cache_key()
    )

    (
        matched_territories_df,
        top_indicators_df,
    ) = get_top_similar_indicators(
        user_question,
        top_k=15,
    )

    logger.debug(
        "Подходящие территории: %s",
        matched_territories_df.to_dict(
            orient="records"
        ),
    )
    logger.debug(
        "Подходящие показатели: %s",
        top_indicators_df.to_dict(
            orient="records"
        ),
    )

    indicators_lines = [
        (
            "- indicator.name = "
            f"{row.get('indicator_name', '')}"
        )
        for _, row in top_indicators_df.iterrows()
    ]

    if not matched_territories_df.empty:
        territories_source = matched_territories_df
    else:
        territories_source = metadata["territories"].head(30)

    territories_lines = [
        (
            f"- {row['territory_name']} | "
            f"тип: {row['territory_type']}"
        )
        for _, row in territories_source.iterrows()
    ]

    periods_lines = [
        (
            f"- {row.get('period_name', '')} | "
            f"тип: {row.get('period_type', '')} | "
            f"start_date: {row.get('start_date', '')} | "
            f"end_date: {row.get('end_date', '')}"
        )
        for _, row in metadata[
            "periods"
        ].head(500).iterrows()
    ]

    units_lines = [
        f"- {unit}"
        for unit in metadata["units"][
            "unit_name"
        ]
        .dropna()
        .astype(str)
        .tolist()
    ]

    sections_lines = [
        (
            f"- {row.get('section_name', '')} | "
            f"категория: {row.get('industry_name', '')}"
        )
        for _, row in metadata[
            "sections"
        ].head(500).iterrows()
    ]

    requested_years = extract_requested_years(
    user_question
)

    periods_df = metadata["periods"].copy()

    if requested_years:
        year_pattern = "|".join(
            re.escape(year)
            for year in requested_years
        )

        matched_periods = periods_df[
            periods_df["period_name"]
            .astype(str)
            .str.contains(
                year_pattern,
                case=False,
                na=False,
                regex=True,
            )
        ]

        if not matched_periods.empty:
            periods_df = matched_periods

    periods_lines = [
        (
            f"- {row['period_name']} | "
            f"тип: {row['period_type']} | "
            f"start_date: {row['start_date']} | "
            f"end_date: {row['end_date']}"
        )
        for _, row in periods_df.head(30).iterrows()
    ]

    return "\n\n".join(
        [
            STATISTICS_SCHEMA_DESCRIPTION,
            (
                "Доступные территории:\n"
                + "\n".join(territories_lines)
            ),
            (
                "Доступные периоды:\n"
                + "\n".join(periods_lines)
            ),
            (
                "Доступные единицы измерения:\n"
                + "\n".join(units_lines)
            ),
            (
                "Доступные секции:\n"
                + "\n".join(sections_lines)
            ),
            (
                "Доступные индикаторы:\n"
                + "\n".join(indicators_lines)
            ),
        ]
    )


def generate_statistics_sql(
    user_question: str,
    conversation_history: str | None = None,
) -> str:
    context = format_statistics_context(
        user_question
    )

    history_block = ""

    if conversation_history:
        history_block = (
            "\n\nИстория диалога:\n"
            f"{conversation_history}"
        )

    user_message = (
        f"{context}"
        f"{history_block}\n\n"
        "Запрос пользователя:\n"
        f"{user_question}\n\n"
        "Сформируй SQL SELECT-запрос."
    )

    logger.debug(
        "Prompt для SQL-модели: %s",
        user_message,
    )

    messages = [
        ChatMessage(
            role="system",
            content=STATISTICS_SQL_SYSTEM_PROMPT,
        ),
        ChatMessage(
            role="user",
            content=user_message,
        ),
    ]

    response = statistics_sql_llm.chat(
    messages)
    raw_sql = response.message.content or ""

    logger.debug(
        "Ответ SQL-модели: %s",
        raw_sql,
    )

    extracted_sql = extract_sql_from_llm_response(
        raw_sql
    )

    return validate_statistics_sql(
        extracted_sql
    )


def generate_statistics_answer(
    user_question: str,
    sql: str,
    dataframe: pd.DataFrame,
) -> str:
    rows_text = dataframe_to_llm_rows(
        dataframe
    )

    messages = [
        ChatMessage(
            role="system",
            content=STATISTICS_ANSWER_SYSTEM_PROMPT,
        ),
        ChatMessage(
            role="user",
            content=(
                "Описание структуры БД:\n"
                f"{STATISTICS_SCHEMA_DESCRIPTION}\n\n"
                "Запрос пользователя:\n"
                f"{user_question}\n\n"
                "SQL-запрос:\n"
                f"{sql}\n\n"
                "Результаты:\n"
                f"{rows_text}"
            ),
        ),
    ]

    response = statistics_answer_llm.chat(
    messages)
    return response.message.content or ""


def generate_statistics_response(
    user_question: str,
    conversation_history: str | None = None,
) -> str:
    try:
        sql = generate_statistics_sql(
            user_question,
            conversation_history=conversation_history,
        )

        logger.info(
            "SQL статистического агента: %s",
            sql,
        )

        dataframe = execute_statistics_sql(sql)

        logger.info(
            "Получено строк статистики: %s",
            len(dataframe),
        )

        return generate_statistics_answer(
            user_question,
            sql,
            dataframe,
        )

    except Exception as error:
        logger.exception(
            "Ошибка статистического агента"
        )
        return (
            "Ошибка при обработке статистического "
            f"запроса: {error}"
        )


def dataframe_to_llm_rows(
    dataframe: pd.DataFrame,
    max_rows: int = 50,
) -> str:
    if dataframe.empty:
        return "Результат пуст."

    lines: list[str] = []

    for row_number, (_, row) in enumerate(
        dataframe.head(max_rows).iterrows(),
        start=1,
    ):
        parts = [
            f"{column}: {row[column]}"
            for column in dataframe.columns
        ]

        lines.append(
            f"Строка {row_number}: "
            + "; ".join(parts)
        )

    return "\n".join(lines)
