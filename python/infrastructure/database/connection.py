from __future__ import annotations

import psycopg2
from psycopg2.extensions import connection

from core.config import PSYCOPG_DB_PARAMS


def create_db_connection() -> connection:
    """
    Создаёт новое соединение с PostgreSQL.

    Важно:
    вызывающий код должен самостоятельно закрыть
    соединение через connection.close().
    """

    print("\n" + "=" * 80)
    print("CHECKPOINT: CREATE DATABASE CONNECTION")
    print("=" * 80)
    print(f"Host: {PSYCOPG_DB_PARAMS.get('host')}")
    print(f"Port: {PSYCOPG_DB_PARAMS.get('port')}")
    print(f"Database: {PSYCOPG_DB_PARAMS.get('database')}")
    print(f"User: {PSYCOPG_DB_PARAMS.get('user')}")

    try:
        db_connection = psycopg2.connect(
            **PSYCOPG_DB_PARAMS
        )

        print("✅ Соединение с PostgreSQL создано")
        return db_connection

    except Exception as error:
        print("❌ Не удалось подключиться к PostgreSQL")
        print(
            f"{type(error).__name__}: {error}"
        )
        raise
