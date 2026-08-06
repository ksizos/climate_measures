from collections.abc import Generator

from psycopg2.extensions import connection as PostgreSQLConnection

from infrastructure.database.connection import (
    create_db_connection,
)


def get_db_connection() -> Generator[
    PostgreSQLConnection,
    None,
    None,
]:
    connection = create_db_connection()

    try:
        yield connection
    finally:
        connection.close()
