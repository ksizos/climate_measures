from __future__ import annotations

from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.postgres import (
    PGVectorStore,
)

from core.config import (
    DB_PARAMS,
    ADAPTATION_TABLE,
)
from infrastructure.llm.embeddings import (
    embed_model,
)


def _resolve_table_name(
    table_name: str | None,
) -> str:
    """
    Возвращает логическое имя PGVector-таблицы.

    Важно:
    LlamaIndex самостоятельно добавляет префикс data_.

    Например:
        table_name="npa_embeddings"

    соответствует физической таблице:
        public.data_npa_embeddings
    """

    selected_table = (
        table_name.strip()
        if table_name and table_name.strip()
        else ADAPTATION_TABLE
    )

    if not selected_table:
        raise ValueError(
            "Не указано имя PGVector-таблицы. "
            "Передай table_name или задай ADAPTATION_TABLE в .env."
        )

    if selected_table.startswith("data_"):
        raise ValueError(
            "В конфигурации PGVector нужно указывать "
            "логическое имя без префикса data_. "
            f"Получено: {selected_table!r}. "
            f"Вероятно, нужно: "
            f"{selected_table.removeprefix('data_')!r}."
        )

    return selected_table


def get_vector_store(
    table_name: str | None = None,
) -> PGVectorStore:
    """
    Подключается к существующей PGVector-таблице.

    Таблицы и индексы при runtime-запросе не создаются.
    """

    selected_table = _resolve_table_name(
        table_name
    )

    return PGVectorStore.from_params(
        database=DB_PARAMS["database"],
        host=DB_PARAMS["host"],
        password=DB_PARAMS["password"],
        port=DB_PARAMS["port"],
        user=DB_PARAMS["user"],
        embed_dim=DB_PARAMS["embed_dim"],

        table_name=selected_table,
        schema_name="public",

        # Таблицы уже заранее созданы и заполнены.
        # Runtime должен только читать их.
        perform_setup=False,

        hnsw_kwargs={
            "hnsw_m": 16,
            "hnsw_ef_construction": 64,
            "hnsw_ef_search": 40,
            "hnsw_dist_method": "vector_cosine_ops",
        },
    )


def load_vector_index(
    table_name: str | None = None,
) -> VectorStoreIndex:
    """
    Загружает LlamaIndex-индекс поверх существующей
    PGVector-таблицы.
    """

    vector_store = get_vector_store(
        table_name=table_name,
    )

    return VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embed_model,
    )
