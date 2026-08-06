import logging
import threading
import time

from psycopg2 import sql
from llama_index.core import (
    StorageContext,
    VectorStoreIndex,
)
from llama_index.vector_stores.postgres import (
    PGVectorStore,
)

from core.config import (
    DATA_PATH,
    DB_PARAMS,
    ADAPTATION_TABLE,
)

from infrastructure.database.connection import (
    create_db_connection,
)
from infrastructure.llm.embeddings import (
    embed_model,
)
from infrastructure.files.excel_reader import (
    process_excel_files,
)
from services.approved_measures import (
    get_approved_documents,
)

logger = logging.getLogger(__name__)

_rebuild_lock = threading.Lock()

def background_rebuild_index() -> None:
    if _rebuild_lock.locked():
        logger.info(
            "Перестроение индекса уже запущено"
        )
        return

    with _rebuild_lock:
        timestamp = int(time.time())

        temp_table = (
            f"climate_embeddings_new_{timestamp}"
        )
        active_table = ADAPTATION_TABLE
        backup_table = (
            f"climate_embeddings_old_{timestamp}"
        )

        logger.info(
            "Запущено перестроение индекса. "
            "Временная таблица: %s",
            temp_table,
        )

        try:
            temp_store = PGVectorStore.from_params(
                table_name=temp_table,
                hnsw_kwargs={
                    "hnsw_m": 16,
                    "hnsw_ef_construction": 64,
                    "hnsw_ef_search": 40,
                    "hnsw_dist_method": (
                        "vector_cosine_ops"
                    ),
                },
                **DB_PARAMS,
            )

            all_documents = process_excel_files(
                DATA_PATH
            )
            all_documents.extend(
                get_approved_documents()
            )

            if not all_documents:
                raise ValueError(
                    "Нет документов для индексации"
                )

            storage_context = (
                StorageContext.from_defaults(
                    vector_store=temp_store,
                )
            )

            VectorStoreIndex.from_documents(
                all_documents,
                storage_context=storage_context,
                embed_model=embed_model,
                show_progress=True,
            )

            logger.info(
                "Временный индекс создан: %s",
                temp_table,
            )

            active_physical_table = (
                f"data_{active_table}"
            )
            temp_physical_table = (
                f"data_{temp_table}"
            )
            backup_physical_table = (
                f"data_{backup_table}"
            )

            connection = create_db_connection()

            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        sql.SQL(
                            "ALTER TABLE IF EXISTS {} "
                            "RENAME TO {}"
                        ).format(
                            sql.Identifier(
                                active_physical_table
                            ),
                            sql.Identifier(
                                backup_physical_table
                            ),
                        )
                    )

                    cursor.execute(
                        sql.SQL(
                            "ALTER TABLE {} "
                            "RENAME TO {}"
                        ).format(
                            sql.Identifier(
                                temp_physical_table
                            ),
                            sql.Identifier(
                                active_physical_table
                            ),
                        )
                    )

                connection.commit()

            except Exception:
                connection.rollback()
                raise

            finally:
                connection.close()

            logger.info(
                "Перестроение завершено. "
                "Резервная таблица: %s",
                backup_physical_table,
            )

        except Exception:
            logger.exception(
                "Ошибка перестроения индекса"
            )
