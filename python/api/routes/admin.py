import threading

import psycopg2
from fastapi import APIRouter
from pydantic import BaseModel, Field

from core.config import PSYCOPG_DB_PARAMS
from services.index_rebuild_service import background_rebuild_index


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


class ExecuteSQLRequest(BaseModel):
    sql: str = Field(
        ...,
        min_length=1,
        description="INSERT-запрос для выполнения в PostgreSQL",
    )


@router.post("/rebuild-index")
async def manual_rebuild() -> dict[str, str]:
    """
    Запускает перестроение векторного индекса
    в отдельном фоновом потоке.
    """
    thread = threading.Thread(
        target=background_rebuild_index,
        name="vector-index-rebuild",
        daemon=True,
    )
    thread.start()

    return {
        "status": "started",
        "message": "Ребилд запущен в фоне",
    }


@router.post("/execute-sql")
def execute_sql(
    request: ExecuteSQLRequest,
) -> dict[str, object]:
    """
    Временно выполняет административные INSERT-запросы.

    В дальнейшем этот endpoint лучше заменить
    специализированным API для добавления данных.
    """
    sql = request.sql.strip()

    try:
        _validate_insert_sql(sql)

        with psycopg2.connect(**PSYCOPG_DB_PARAMS) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                rows_affected = cursor.rowcount

        return {
            "success": True,
            "message": (
                f"Успешно добавлено записей: {rows_affected}"
            ),
            "rows_affected": rows_affected,
        }

    except ValueError as exc:
        return {
            "success": False,
            "error": str(exc),
            "message": f"Ошибка проверки SQL: {exc}",
        }

    except psycopg2.Error as exc:
        return {
            "success": False,
            "error": str(exc),
            "message": f"Ошибка PostgreSQL: {exc}",
        }

    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "message": f"Ошибка выполнения SQL: {exc}",
        }


def _validate_insert_sql(sql: str) -> None:
    """
    Выполняет минимальную проверку административного SQL.

    Проверка не делает произвольный SQL полностью безопасным,
    но сохраняет текущую логику endpoint и отсекает очевидно
    неподходящие запросы.
    """
    normalized_sql = sql.strip()
    normalized_lower = normalized_sql.lower()

    if not normalized_sql:
        raise ValueError("SQL-запрос не может быть пустым")

    if not normalized_lower.startswith("insert into"):
        raise ValueError("Разрешены только INSERT-запросы")

    # Запрещаем несколько SQL-команд в одном запросе.
    statements = [
        statement.strip()
        for statement in normalized_sql.split(";")
        if statement.strip()
    ]

    if len(statements) != 1:
        raise ValueError(
            "Разрешено выполнять только один SQL-запрос"
        )

    forbidden_fragments = (
        "--",
        "/*",
        "*/",
        " drop ",
        " alter ",
        " truncate ",
        " delete ",
        " update ",
        " grant ",
        " revoke ",
        " create ",
    )

    sql_for_check = f" {normalized_lower} "

    for fragment in forbidden_fragments:
        if fragment in sql_for_check:
            raise ValueError(
                f"SQL содержит запрещенную конструкцию: "
                f"{fragment.strip()}"
            )
