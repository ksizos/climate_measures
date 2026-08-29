import logging

import pandas as pd
import json
import re


from infrastructure.database.sql_security import (
    extract_sql_from_llm_response,
    validate_statistics_sql,
)

from prompts.statistics import (
    STATISTICS_ANSWER_SYSTEM_PROMPT,
    STATISTICS_QUERY_PLANNER_SYSTEM_PROMPT,
    STATISTICS_SCHEMA_DESCRIPTION,
    STATISTICS_SQL_SYSTEM_PROMPT,
)

from infrastructure.llm.provider import (
    chat_text,
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


logger = logging.getLogger(__name__)


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



def generate_statistics_query_plan(
    user_question: str,
    conversation_history: str | None = None,
) -> dict:
    history_block = ""

    if conversation_history:
        history_block = (
            "\n\nИстория диалога:\n"
            f"{conversation_history}"
        )

    raw_plan = chat_text(
        system_prompt=(
            STATISTICS_QUERY_PLANNER_SYSTEM_PROMPT
        ),
        user_prompt=(
            f"Запрос пользователя:\n"
            f"{user_question}"
            f"{history_block}"
        ),
        temperature=0.0,
        max_new_tokens=350,
    )

    logger.info(
        "RAW план статистического запроса:\n%s",
        raw_plan,
    )

    cleaned = raw_plan.strip()

    # На случай, если модель всё же вернула ```json.
    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
    ).strip()

    try:
        plan = json.loads(cleaned)

    except (json.JSONDecodeError, TypeError):
        logger.warning(
            "Не удалось разобрать JSON planner. "
            "Используем исходный запрос."
        )

        return {
            "indicator_queries": [
                user_question
            ],
            "territory_query": None,
            "date_from": None,
            "date_to": None,
            "calculation": user_question,
        }

    indicator_queries = plan.get(
        "indicator_queries"
    )

    if not isinstance(
        indicator_queries,
        list,
    ):
        indicator_queries = []

    indicator_queries = [
        str(value).strip()
        for value in indicator_queries
        if str(value).strip()
    ]

    if not indicator_queries:
        indicator_queries = [
            user_question
        ]

    result = {
        "indicator_queries":
            indicator_queries,

        "territory_query":
            plan.get(
                "territory_query"
            ),

        "date_from":
            plan.get(
                "date_from"
            ),

        "date_to":
            plan.get(
                "date_to"
            ),

        "calculation":
            str(
                plan.get(
                    "calculation",
                    "",
                )
            ).strip(),
    }

    logger.info(
        "План статистического запроса: %s",
        result,
    )

    return result


def format_statistics_context(
    user_question: str,
    query_plan: dict,
) -> str:
    """
    Формирует контекст для LLM,
    которая генерирует SQL-запрос.

    Использует:
    - JSON-план запроса;
    - найденные территории;
    - подходящие индикаторы;
    - период;
    - дополнительные метаданные БД.
    """

    # ---------------------------------------------------------
    # 1. Загружаем общие метаданные статистики
    # ---------------------------------------------------------

    metadata = get_statistics_metadata(
        statistics_cache_key()
    )

    # ---------------------------------------------------------
    # 2. Забираем данные из JSON-плана
    # ---------------------------------------------------------

    indicator_queries = (
        query_plan.get(
            "indicator_queries"
        )
        or [user_question]
    )

    date_from = query_plan.get(
        "date_from"
    )

    date_to = query_plan.get(
        "date_to"
    )

    calculation = str(
        query_plan.get(
            "calculation",
            ""
        )
        or ""
    ).strip()

    territory_query = query_plan.get(
        "territory_query"
    )

    # ---------------------------------------------------------
    # 3. Ищем территории и индикаторы
    #
    # Для каждой indicator_query RapidFuzz ищет
    # подходящие показатели отдельно.
    #
    # Также список показателей предварительно
    # ограничивается территорией и периодом.
    # ---------------------------------------------------------

    (
        matched_territories_df,
        top_indicators_df,
    ) = get_top_similar_indicators(
        user_question=user_question,
        indicator_queries=indicator_queries,
        date_from=date_from,
        date_to=date_to,
        top_k_per_query=5,
    )

    logger.info(
        "Подходящие территории: %s",
        matched_territories_df.to_dict(
            orient="records"
        ),
    )

    logger.info(
        "Подходящие показатели: %s",
        top_indicators_df.to_dict(
            orient="records"
        ),
    )

    # ---------------------------------------------------------
    # 4. Формируем описание JSON-плана
    # ---------------------------------------------------------

    indicator_queries_text = (
        ", ".join(
            str(query)
            for query in indicator_queries
        )
        if indicator_queries
        else "не определены"
    )

    plan_lines = [
        (
            "- Территория из плана: "
            f"{territory_query or 'не указана'}"
        ),
        (
            "- Требуемые смысловые показатели: "
            f"{indicator_queries_text}"
        ),
        (
            "- Начало периода: "
            f"{date_from or 'не указано'}"
        ),
        (
            "- Конец периода: "
            f"{date_to or 'не указано'}"
        ),
        (
            "- Требуемый расчёт или анализ: "
            f"{calculation or 'получить значение показателя'}"
        ),
    ]

    # ---------------------------------------------------------
    # 5. Формируем полную информацию
    # о найденных кандидатах
    # ---------------------------------------------------------

    indicators_lines: list[str] = []

    for _, row in top_indicators_df.iterrows():
        similarity = row.get(
            "similarity",
            0,
        )

        try:
            similarity_text = (
                f"{float(similarity):.1f}"
            )
        except (
            TypeError,
            ValueError,
        ):
            similarity_text = str(
                similarity
            )

        indicators_lines.append(
            (
                "- "
                f"indicator.id = "
                f"{row.get('indicator_id', '')} | "
                f"name = "
                f"{row.get('indicator_name', '')} | "
                f"unit = "
                f"{row.get('unit_name', '')} | "
                f"section = "
                f"{row.get('section_name', '')} | "
                f"industry = "
                f"{row.get('industry_name', '')} | "
                f"matched_query = "
                f"{row.get('matched_query', '')} | "
                f"similarity = "
                f"{similarity_text}"
            )
        )

    if not indicators_lines:
        indicators_lines = [
            "- Подходящие индикаторы не найдены."
        ]

    # ---------------------------------------------------------
    # 6. Территории
    #
    # Если RapidFuzz нашёл конкретные территории,
    # модели показываем только их.
    #
    # Иначе даём небольшой общий список.
    # ---------------------------------------------------------

    if not matched_territories_df.empty:
        territories_source = (
            matched_territories_df
        )
    else:
        territories_source = (
            metadata[
                "territories"
            ].head(30)
        )

    territories_lines: list[str] = []

    for _, row in (
        territories_source.iterrows()
    ):
        territory_id = row.get(
            "territory_id",
            ""
        )

        territory_name = row.get(
            "territory_name",
            ""
        )

        territory_type = row.get(
            "territory_type",
            ""
        )

        territories_lines.append(
            (
                "- "
                f"territory.id = "
                f"{territory_id} | "
                f"name = {territory_name} | "
                f"тип = {territory_type}"
            )
        )

    # ---------------------------------------------------------
    # 7. Периоды
    #
    # Если planner определил диапазон дат,
    # показываем модели только пересекающиеся
    # с ним периоды.
    # ---------------------------------------------------------

    periods_df = metadata[
        "periods"
    ].copy()

    if (
        not periods_df.empty
        and (
            date_from
            or date_to
        )
    ):
        periods_df[
            "_start_date"
        ] = pd.to_datetime(
            periods_df[
                "start_date"
            ],
            errors="coerce",
        )

        periods_df[
            "_end_date"
        ] = pd.to_datetime(
            periods_df[
                "end_date"
            ],
            errors="coerce",
        )

        period_mask = pd.Series(
            True,
            index=periods_df.index,
        )

        if date_from:
            requested_start = (
                pd.to_datetime(
                    date_from,
                    errors="coerce",
                )
            )

            if not pd.isna(
                requested_start
            ):
                period_mask &= (
                    periods_df[
                        "_end_date"
                    ].isna()
                    |
                    (
                        periods_df[
                            "_end_date"
                        ]
                        >= requested_start
                    )
                )

        if date_to:
            requested_end = (
                pd.to_datetime(
                    date_to,
                    errors="coerce",
                )
            )

            if not pd.isna(
                requested_end
            ):
                period_mask &= (
                    periods_df[
                        "_start_date"
                    ].isna()
                    |
                    (
                        periods_df[
                            "_start_date"
                        ]
                        <= requested_end
                    )
                )

        matched_periods_df = (
            periods_df[
                period_mask
            ]
        )

        if not matched_periods_df.empty:
            periods_df = (
                matched_periods_df
            )

    periods_lines = [
        (
            f"- {row.get('period_name', '')} | "
            f"тип = "
            f"{row.get('period_type', '')} | "
            f"start_date = "
            f"{row.get('start_date', '')} | "
            f"end_date = "
            f"{row.get('end_date', '')}"
        )
        for _, row
        in periods_df.head(
            40
        ).iterrows()
    ]

    # ---------------------------------------------------------
    # 8. Единицы измерения
    # ---------------------------------------------------------

    units_lines = [
        f"- {unit}"
        for unit
        in metadata[
            "units"
        ][
            "unit_name"
        ]
        .dropna()
        .astype(str)
        .tolist()
    ]

    # ---------------------------------------------------------
    # 9. Секции
    #
    # Общий список оставляем как дополнительную
    # справочную информацию для SQL-модели.
    # ---------------------------------------------------------

    sections_lines = [
        (
            f"- "
            f"{row.get('section_name', '')} | "
            f"категория = "
            f"{row.get('industry_name', '')}"
        )
        for _, row
        in metadata[
            "sections"
        ].head(
            200
        ).iterrows()
    ]

    # ---------------------------------------------------------
    # 10. Собираем итоговый контекст
    # ---------------------------------------------------------

    return "\n\n".join(
        [
            STATISTICS_SCHEMA_DESCRIPTION,

            (
                "План статистического запроса:\n"
                + "\n".join(
                    plan_lines
                )
            ),

            (
                "Подходящие территории:\n"
                + "\n".join(
                    territories_lines
                )
            ),

            (
                "Подходящие периоды:\n"
                + "\n".join(
                    periods_lines
                )
            ),

            (
                "Доступные единицы измерения:\n"
                + "\n".join(
                    units_lines
                )
            ),

            (
                "Доступные секции:\n"
                + "\n".join(
                    sections_lines
                )
            ),

            (
                "Кандидаты индикаторов, "
                "найденные для запроса:\n"
                + "\n".join(
                    indicators_lines
                )
            ),
        ]
    )


def generate_statistics_sql(
    user_question: str,
    conversation_history: str | None = None,
) -> str:
    query_plan = (
        generate_statistics_query_plan(
            user_question,
            conversation_history=(
                conversation_history
            ),
        )
    )

    context = format_statistics_context(
        user_question,
        query_plan,
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

    raw_sql = chat_text(
        system_prompt=(
            STATISTICS_SQL_SYSTEM_PROMPT
        ),
        user_prompt=user_message,
        temperature=0.0,
        max_new_tokens=700,
    )  

    logger.info(
        "RAW ответ SQL-модели:\n%s",
        raw_sql,
    )

    extracted_sql = extract_sql_from_llm_response(
        raw_sql
    )
    logger.info(
        "Извлечённый SQL:\n%s",
        extracted_sql,
    )
    print(extracted_sql)
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

    user_prompt = (
        "Описание структуры БД:\n"
        f"{STATISTICS_SCHEMA_DESCRIPTION}\n\n"

        "Запрос пользователя:\n"
        f"{user_question}\n\n"

        "Выполненный SQL-запрос:\n"
        f"{sql}\n\n"

        "Полученные результаты:\n"
        f"{rows_text}"
    )

    return chat_text(
        system_prompt=(
            STATISTICS_ANSWER_SYSTEM_PROMPT
        ),
        user_prompt=user_prompt,
        temperature=0.1,
        max_new_tokens=1200,
    )


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
