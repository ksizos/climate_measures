import re

FORBIDDEN_SQL_TOKENS = (
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "grant",
    "revoke",
)

def extract_sql_from_llm_response(
    text: str,
) -> str:
    if not text:
        return ""

    sql = text.strip()

    # Убираем Markdown-блоки:
    # ```sql
    # ```postgresql
    # ```
    sql = re.sub(
        r"^```(?:sql|postgresql)?\s*",
        "",
        sql,
        flags=re.IGNORECASE,
    )

    sql = re.sub(
        r"\s*```$",
        "",
        sql,
    )

    sql = sql.strip()

    # Если модель всё-таки добавила пояснение
    # перед SQL, берём текст начиная
    # с первого SELECT или WITH.
    match = re.search(
        r"\b(SELECT|WITH)\b",
        sql,
        flags=re.IGNORECASE,
    )

    if match:
        sql = sql[
            match.start():
        ]

    # Исправление иногда возникающих
    # двойных кавычек у DATE.
    sql = re.sub(
        r"DATE\s+''(\d{4}-\d{2}-\d{2})''",
        r"DATE '\1'",
        sql,
        flags=re.IGNORECASE,
    )

    # Убираем возможный закрывающий
    # Markdown-блок после SQL.
    sql = re.sub(
        r"\s*```\s*$",
        "",
        sql,
    )

    return sql.strip()


def validate_statistics_sql(
    sql: str,
) -> str:
    if not sql or not sql.strip():
        raise ValueError(
            "SQL-запрос не может быть пустым"
        )

    sql_clean = sql.strip().rstrip(";")
    sql_lower = sql_clean.lower()

    if not (
        sql_lower.startswith("select")
        or sql_lower.startswith("with")
    ):
        raise ValueError(
            "Статистический агент может выполнять "
            "только SELECT-запросы"
        )

    padded_sql = f" {sql_lower} "

    for token in FORBIDDEN_SQL_TOKENS:
        if re.search(
            rf"\b{re.escape(token)}\b",
            padded_sql,
        ):
            raise ValueError(
                "Обнаружен запрещённый SQL-оператор"
            )

    if (
        "i.full_name" in sql_lower
        or "indicator.full_name" in sql_lower
    ):
        raise ValueError(
            "В таблице indicator нет поля full_name. "
            "Используй indicator.name."
        )

    if (
        "t.territory_name" in sql_lower
        or "territory.territory_name" in sql_lower
    ):
        raise ValueError(
            "В таблице territory нет поля territory_name. "
            "Используй territory.name."
        )

    if ";" in sql_clean:
        raise ValueError(
            "Разрешён только один SQL-запрос"
        )

    return sql_clean
