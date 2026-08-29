from functools import lru_cache
from typing import Any

import pandas as pd

from infrastructure.database.connection import (
    create_db_connection,
)
from infrastructure.database.sql_security import (
    validate_statistics_sql,
)
from services.statistics_cache import (
    statistics_cache_key,
)


StatisticsMetadata = dict[str, pd.DataFrame]


@lru_cache(maxsize=1)
def get_statistics_metadata(
    _cache_key: int,
) -> StatisticsMetadata:
    connection = create_db_connection()

    try:
        indicators_df = pd.read_sql_query(
            """
            SELECT
                i.id AS indicator_id,
                i.name AS indicator_name,
                s.name AS section_name,
                u.name AS unit_name,
                COALESCE(ind.name, '') AS industry_name
            FROM indicator i
            JOIN section s
                ON s.id = i.section_id
            JOIN unit u
                ON u.id = i.unit_id
            LEFT JOIN industry ind
                ON ind.id = s.industry_id
            ORDER BY s.name, i.name
            """,
            connection,
        )

        territories_df = pd.read_sql_query(
            """
            SELECT
                t.id AS territory_id,
                t.name AS territory_name,
                COALESCE(tt.name, '') AS territory_type
            FROM territory t
            LEFT JOIN territory_type tt
                ON tt.id = t.territory_type_id
            ORDER BY t.name
            """,
            connection,
        )

        periods_df = pd.read_sql_query(
            """
            SELECT
                p.name AS period_name,
                COALESCE(pt.name, '') AS period_type,
                p.start_date,
                p.end_date
            FROM period p
            LEFT JOIN period_type pt
                ON pt.id = p.period_type_id
            ORDER BY p.name
            """,
            connection,
        )

        units_df = pd.read_sql_query(
            """
            SELECT name AS unit_name
            FROM unit
            ORDER BY name
            """,
            connection,
        )

        sections_df = pd.read_sql_query(
            """
            SELECT
                s.name AS section_name,
                COALESCE(ind.name, '') AS industry_name
            FROM section s
            LEFT JOIN industry ind
                ON ind.id = s.industry_id
            ORDER BY s.name
            """,
            connection,
        )

        return {
            "indicators": indicators_df,
            "territories": territories_df,
            "periods": periods_df,
            "units": units_df,
            "sections": sections_df,
        }

    finally:
        connection.close()

def clear_statistics_metadata_cache() -> None:
    """
    Очищает кэш метаданных статистики.
    """
    get_statistics_metadata.cache_clear()

def get_indicators_for_territories(
    territory_names: list[str],
    date_from: str | None = None,
    date_to: str | None = None,
) -> pd.DataFrame:

    connection = create_db_connection()

    try:
        conditions: list[str] = []
        params: list[Any] = []

        if territory_names:
            conditions.append(
                "t.name = ANY(%s)"
            )

            params.append(
                territory_names
            )

        if date_from:
            conditions.append(
                "p.end_date >= %s"
            )

            params.append(
                date_from
            )

        if date_to:
            conditions.append(
                "p.start_date <= %s"
            )

            params.append(
                date_to
            )

        where_sql = ""

        if conditions:
            where_sql = (
                "WHERE "
                + " AND ".join(
                    conditions
                )
            )

        sql = f"""
            SELECT DISTINCT
                i.id AS indicator_id,
                i.name AS indicator_name,
                s.name AS section_name,
                u.name AS unit_name,
                COALESCE(
                    ind.name,
                    ''
                ) AS industry_name
            FROM statistic st

            JOIN territory t
                ON t.id = st.territory_id

            JOIN indicator i
                ON i.id = st.indicator_id

            JOIN section s
                ON s.id = i.section_id

            JOIN unit u
                ON u.id = i.unit_id

            LEFT JOIN industry ind
                ON ind.id = s.industry_id

            JOIN period p
                ON p.id = st.period_id

            {where_sql}

            ORDER BY i.name
        """

        return pd.read_sql_query(
            sql,
            connection,
            params=tuple(params),
        )

    finally:
        connection.close()


def execute_statistics_sql(
    sql: str,
) -> pd.DataFrame:
    validated_sql = validate_statistics_sql(sql)

    connection = create_db_connection()

    try:
        return pd.read_sql_query(
            validated_sql,
            connection,
        )

    finally:
        connection.close()
