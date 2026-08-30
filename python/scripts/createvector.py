from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

import pandas as pd

from core.config import (
    DB_PARAMS,
    EMBED_MODEL,
    DATA_PATH,
    ADAPTATION_TABLE,
    NPA_TABLE,
    METHOD_DOCS_TABLE,
    INTERNET_RESOURCES_TABLE,
    FLOOD_OBJECTS_TABLE,
)

from llama_index.core import (
    Document,
    Settings,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.node_parser import (
    SentenceSplitter,
)
from llama_index.core.schema import (
    TextNode,
)
from llama_index.embeddings.huggingface import (
    HuggingFaceEmbedding,
)
from llama_index.vector_stores.postgres import (
    PGVectorStore,
)


# =====================================================
# PATHS
# =====================================================

PYTHON_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

DATA_DIR = Path(DATA_PATH)

if not DATA_DIR.is_absolute():
    DATA_DIR = (
        PYTHON_ROOT
        / DATA_DIR
    ).resolve()

NPA_CATALOG_FILE = (
    DATA_DIR
    / "NPA_TABLE.xlsx"
)

NPA_DOCUMENTS_DIR = (
    DATA_DIR
    / "npa_documents"
)

METHOD_CATALOG_FILE = (
    DATA_DIR
    / "METHOD_TABLE.xlsx"
)

METHOD_DOCUMENTS_DIR = (
    DATA_DIR
    / "method_documents"
)

# =====================================================
# HELPERS
# =====================================================

def cell_to_text(
    value: Any,
) -> str:
    """
    Безопасно преобразует значение Excel
    в строку.
    """

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    if isinstance(
        value,
        pd.Timestamp,
    ):
        return value.strftime(
            "%Y-%m-%d"
        )

    if isinstance(
        value,
        float,
    ) and value.is_integer():
        return str(
            int(value)
        )

    return str(
        value
    ).strip()


def normalize_document_id(
    value: Any,
) -> int | str:
    """
    Сохраняет обычный числовой id как int.
    Если id строковый — возвращает строку.
    """

    if value is None:
        raise ValueError(
            "Пустой id документа."
        )

    try:
        if pd.isna(value):
            raise ValueError(
                "Пустой id документа."
            )
    except TypeError:
        pass

    if isinstance(value, int):
        return value

    if isinstance(
        value,
        float,
    ) and value.is_integer():
        return int(value)

    text = str(
        value
    ).strip()

    if not text:
        raise ValueError(
            "Пустой id документа."
        )

    if text.isdigit():
        return int(text)

    return text


def compact_metadata(
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """
    Убирает пустые значения metadata.
    """

    result: dict[
        str,
        Any,
    ] = {}

    for key, value in metadata.items():
        if value is None:
            continue

        if (
            isinstance(value, str)
            and not value.strip()
        ):
            continue

        result[key] = value

    return result


# =====================================================
# EMBEDDING MODEL
# =====================================================

def initialize_embedding_model():
    print(
        "\n==================================="
    )
    print(
        "INITIALIZE EMBEDDING MODEL"
    )
    print(
        "==================================="
    )

    if not EMBED_MODEL:
        raise RuntimeError(
            "EMBED_MODEL не задан в .env"
        )

    print(
        "MODEL:",
        EMBED_MODEL,
    )

    embed_model = (
        HuggingFaceEmbedding(
            model_name=EMBED_MODEL
        )
    )

    Settings.embed_model = (
        embed_model
    )

    test_embedding = (
        embed_model
        .get_text_embedding(
            "Тест"
        )
    )

    print(
        "Embedding dimension:",
        len(test_embedding),
    )

    if (
        len(test_embedding)
        != DB_PARAMS["embed_dim"]
    ):
        raise RuntimeError(
            "Wrong embedding dimension. "
            f"Expected "
            f"{DB_PARAMS['embed_dim']}, "
            f"got "
            f"{len(test_embedding)}"
        )

    print(
        "Embedding model loaded"
    )


# =====================================================
# GENERIC EXCEL LOADER
# Старое поведение для остальных таблиц
# =====================================================

def read_excel_as_documents(
    file_path: str | Path,
) -> list[Document]:

    file_path = Path(
        file_path
    )

    print(
        "\n==================================="
    )
    print(
        "READ FILE"
    )
    print(
        "==================================="
    )
    print(
        file_path
    )

    df = pd.read_excel(
        file_path
    )

    print(
        "\nColumns:"
    )

    for col in df.columns:
        print(
            " -",
            col,
        )

    documents: list[
        Document
    ] = []

    embed_columns = [
        "Проблема",
        "Наименование мероприятий",
        "Митигационный эффект",
        "Адаптационный эффект",
    ]

    meta_columns = [
        "Наименование района",
        "Агроклиматические условия района",
        "Ответственная организация",
        "Источник",
    ]

    for index, row in (
        df.iterrows()
    ):
        text_parts: list[str] = []

        for col in embed_columns:
            if col not in df.columns:
                continue

            value = cell_to_text(
                row[col]
            )

            if value:
                text_parts.append(
                    f"{col}: {value}"
                )

        # Если специальных полей нет,
        # берём всю строку.
        if not text_parts:
            for col in df.columns:
                value = cell_to_text(
                    row[col]
                )

                if value:
                    text_parts.append(
                        f"{col}: {value}"
                    )

        text = "\n".join(
            text_parts
        ).strip()

        if not text:
            continue

        metadata: dict[
            str,
            Any,
        ] = {
            "source":
                file_path.name,
            "row_index":
                int(index),
            "file_type":
                "excel",
        }

        for col in meta_columns:
            if col not in df.columns:
                continue

            value = cell_to_text(
                row[col]
            )

            if value:
                metadata[
                    f"meta_{col}"
                ] = value

        documents.append(
            Document(
                text=text,
                metadata=metadata,
            )
        )

    print(
        "Documents:",
        len(documents),
    )

    return documents


def load_documents(
    files,
) -> list[Document]:

    if isinstance(
        files,
        (str, Path),
    ):
        files = [
            files
        ]

    all_documents: list[
        Document
    ] = []

    for file_path in files:
        all_documents.extend(
            read_excel_as_documents(
                file_path
            )
        )

    print(
        "\nTOTAL DOCUMENTS:",
        len(all_documents),
    )

    return all_documents


# =====================================================
# PGVECTOR
# =====================================================

def create_vector_store(
    table_name: str,
) -> PGVectorStore:

    if not table_name:
        raise ValueError(
            "Не указано имя vector table."
        )

    print(
        "\n==================================="
    )
    print(
        "CONNECT PGVECTOR"
    )
    print(
        "==================================="
    )
    print(
        "TABLE:",
        table_name,
    )

    vector_store = (
        PGVectorStore.from_params(
            database=(
                DB_PARAMS[
                    "database"
                ]
            ),
            host=(
                DB_PARAMS[
                    "host"
                ]
            ),
            password=(
                DB_PARAMS[
                    "password"
                ]
            ),
            port=(
                DB_PARAMS[
                    "port"
                ]
            ),
            user=(
                DB_PARAMS[
                    "user"
                ]
            ),
            table_name=table_name,
            schema_name="public",
            embed_dim=(
                DB_PARAMS[
                    "embed_dim"
                ]
            ),
            perform_setup=True,
            hnsw_kwargs={
                "hnsw_m": 16,
                "hnsw_ef_construction":
                    64,
                "hnsw_ef_search":
                    40,
                "hnsw_dist_method":
                    "vector_cosine_ops",
            },
        )
    )

    print(
        "PGVectorStore READY"
    )

    return vector_store


def create_index_from_nodes(
    *,
    nodes,
    table_name: str,
):
    if not nodes:
        print(
            "NO NODES CREATED"
        )
        return None

    print(
        "\n==================================="
    )
    print(
        "CREATE STORAGE CONTEXT"
    )
    print(
        "==================================="
    )

    vector_store = (
        create_vector_store(
            table_name
        )
    )

    storage_context = (
        StorageContext.from_defaults(
            vector_store=(
                vector_store
            )
        )
    )

    print(
        "\n==================================="
    )
    print(
        "START INDEXING"
    )
    print(
        "==================================="
    )

    index = VectorStoreIndex(
        nodes=nodes,
        storage_context=(
            storage_context
        ),
        show_progress=True,
    )

    print(
        "\n==================================="
    )
    print(
        "INDEX CREATED"
    )
    print(
        "==================================="
    )
    print(
        "TABLE:",
        table_name,
    )
    print(
        "NODES:",
        len(nodes),
    )

    return index


# =====================================================
# GENERIC INDEX
# =====================================================

def create_vector_index(
    files,
    table_name: str,
):
    documents = load_documents(
        files
    )

    if not documents:
        print(
            "NO DOCUMENTS"
        )
        return None

    parser = SentenceSplitter(
        chunk_size=4096,
        chunk_overlap=0,
    )

    nodes = (
        parser
        .get_nodes_from_documents(
            documents
        )
    )

    print(
        "NODES:",
        len(nodes),
    )

    return create_index_from_nodes(
        nodes=nodes,
        table_name=table_name,
    )


# =====================================================
# NPA CATALOG
# =====================================================

NPA_REQUIRED_COLUMNS = {
    "id",
    "Дата опубликования",
    "№",
    "Вид НПА",
    "Орган гос власти",
    "Название",
    "Преамбула",
    "input_file",
}


def validate_npa_dataframe(
    df: pd.DataFrame,
) -> None:

    missing = (
        NPA_REQUIRED_COLUMNS
        - set(df.columns)
    )

    if missing:
        raise ValueError(
            "В NPA_TABLE.xlsx "
            "отсутствуют колонки: "
            + ", ".join(
                sorted(missing)
            )
        )

    if df["id"].isna().any():
        raise ValueError(
            "В NPA_TABLE.xlsx "
            "есть строки с пустым id."
        )

    normalized_ids = [
        normalize_document_id(
            value
        )
        for value
        in df["id"].tolist()
    ]

    if (
        len(normalized_ids)
        != len(
            set(
                str(value)
                for value
                in normalized_ids
            )
        )
    ):
        raise ValueError(
            "В NPA_TABLE.xlsx "
            "id документов должны "
            "быть уникальными."
        )


def npa_common_metadata(
    row: pd.Series,
) -> dict[str, Any]:

    npa_id = str(
        normalize_document_id(
            row["id"]
        )
    )

    metadata = {
        "knowledge_type":
            "npa",

        "npa_id":
            npa_id,

        "title":
            cell_to_text(
                row[
                    "Название"
                ]
            ),

        "document_type":
            cell_to_text(
                row[
                    "Вид НПА"
                ]
            ),

        "authority":
            cell_to_text(
                row[
                    "Орган гос власти"
                ]
            ),

        "number":
            cell_to_text(
                row[
                    "№"
                ]
            ),

        "date":
            cell_to_text(
                row[
                    "Дата опубликования"
                ]
            ),

        "url":
            cell_to_text(
                row[
                    "Преамбула"
                ]
            ),

        "input_file":
            cell_to_text(
                row[
                    "input_file"
                ]
            ),
    }

    return compact_metadata(
        metadata
    )


def create_npa_catalog_documents(
    df: pd.DataFrame,
) -> list[Document]:

    documents: list[
        Document
    ] = []

    for row_index, row in (
        df.iterrows()
    ):
        metadata = (
            npa_common_metadata(
                row
            )
        )

        metadata.update(
            {
                "record_type":
                    "catalog",
                "source":
                    NPA_CATALOG_FILE.name,
                "row_index":
                    int(row_index),
                "file_type":
                    "excel",
            }
        )

        text_parts = [
            (
                "Вид НПА: "
                + cell_to_text(
                    row["Вид НПА"]
                )
            ),
            (
                "Орган государственной "
                "власти: "
                + cell_to_text(
                    row[
                        "Орган гос власти"
                    ]
                )
            ),
            (
                "Номер: "
                + cell_to_text(
                    row["№"]
                )
            ),
            (
                "Дата опубликования: "
                + cell_to_text(
                    row[
                        "Дата опубликования"
                    ]
                )
            ),
            (
                "Название: "
                + cell_to_text(
                    row["Название"]
                )
            ),
        ]

        text = "\n".join(
            value
            for value
            in text_parts
            if not value.endswith(
                ": "
            )
        )

        documents.append(
            Document(
                text=text,
                metadata=metadata,
            )
        )

    return documents


# =====================================================
# NPA FULL DOCUMENT CONTENT
# =====================================================

SUPPORTED_NPA_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".md",
}


def create_npa_content_documents(
    df: pd.DataFrame,
) -> list[Document]:

    documents: list[
        Document
    ] = []

    NPA_DOCUMENTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for _, row in df.iterrows():

        metadata_base = (
            npa_common_metadata(
                row
            )
        )

        npa_id = (
            metadata_base[
                "npa_id"
            ]
        )

        input_file = (
            metadata_base.get(
                "input_file",
                "",
            )
        )

        if not input_file:
            print(
                "WARNING: "
                f"NPA id={npa_id}: "
                "input_file не указан. "
                "Будет создана только "
                "catalog-запись."
            )
            continue

        file_path = Path(
            input_file
        )

        if not file_path.is_absolute():
            file_path = (
                NPA_DOCUMENTS_DIR
                / file_path
            )

        file_path = (
            file_path.resolve()
        )

        if not file_path.exists():
            print(
                "WARNING: "
                f"NPA id={npa_id}: "
                "файл не найден: "
                f"{file_path}"
            )
            continue

        if (
            file_path.suffix.lower()
            not in
            SUPPORTED_NPA_EXTENSIONS
        ):
            print(
                "WARNING: "
                f"NPA id={npa_id}: "
                "неподдерживаемый формат: "
                f"{file_path.suffix}"
            )
            continue

        print(
            "\nREAD NPA CONTENT:"
        )
        print(
            f"  id={npa_id}"
        )
        print(
            f"  file={file_path.name}"
        )

        try:
            loaded_documents = (
                SimpleDirectoryReader(
                    input_files=[
                        str(file_path)
                    ],
                    raise_on_error=True,
                )
                .load_data()
            )
        except Exception as exc:
            print(
                "WARNING: "
                f"не удалось прочитать "
                f"{file_path.name}: "
                f"{exc}"
            )
            continue

        added_parts = 0

        for part_index, loaded in (
            enumerate(
                loaded_documents,
                start=1,
            )
        ):
            text = (
                loaded.text
                or ""
            ).strip()

            if not text:
                continue

            metadata = dict(
                metadata_base
            )

            metadata.update(
                {
                    "record_type":
                        "content",
                    "source":
                        file_path.name,
                    "file_type":
                        file_path
                        .suffix
                        .lower()
                        .lstrip("."),
                    "content_part":
                        part_index,
                }
            )

            loaded_metadata = (
                getattr(
                    loaded,
                    "metadata",
                    {},
                )
                or {}
            )

            # PDF reader обычно сохраняет
            # номер/метку страницы.
            for key in (
                "page_label",
                "page_number",
            ):
                if key not in (
                    loaded_metadata
                ):
                    continue

                value = (
                    loaded_metadata[
                        key
                    ]
                )

                if value is not None:
                    metadata[
                        key
                    ] = value

            documents.append(
                Document(
                    text=text,
                    metadata=(
                        compact_metadata(
                            metadata
                        )
                    ),
                )
            )

            added_parts += 1

        print(
            "  extracted parts:",
            added_parts,
        )

        if added_parts == 0:
            print(
                "WARNING: "
                f"{file_path.name} "
                "прочитан, но текст "
                "не извлечён. "
                "Возможно, это скан."
            )

    return documents


# =====================================================
# NPA NODES
# =====================================================

def create_npa_nodes(
    catalog_documents:
        list[Document],
    content_documents:
        list[Document],
):

    nodes = []

    # -----------------------------------------
    # CATALOG:
    # одна строка Excel = один node
    # -----------------------------------------

    for document in (
        catalog_documents
    ):
        npa_id = (
            document.metadata[
                "npa_id"
            ]
        )

        node = TextNode(
            id_=(
                f"npa-catalog-"
                f"{npa_id}"
            ),
            text=document.text,
            metadata=(
                document.metadata
            ),
        )

        nodes.append(
            node
        )

    # -----------------------------------------
    # CONTENT:
    # режем полный текст
    # -----------------------------------------

    splitter = SentenceSplitter(
        chunk_size=1000,
        chunk_overlap=120,
    )

    content_nodes = (
        splitter
        .get_nodes_from_documents(
            content_documents
        )
    )

    chunk_counters: dict[
        str,
        int,
    ] = {}

    for node in content_nodes:

        npa_id = (
            node.metadata.get(
                "npa_id"
            )
        )

        key = str(
            npa_id
        )

        chunk_index = (
            chunk_counters.get(
                key,
                0,
            )
        )

        node.metadata[
            "chunk_index"
        ] = chunk_index

        node.id_ = (
            f"npa-content-"
            f"{key}-"
            f"{chunk_index}"
        )

        chunk_counters[
            key
        ] = (
            chunk_index
            + 1
        )

        nodes.append(
            node
        )

    print(
        "\nNPA catalog nodes:",
        len(catalog_documents),
    )

    print(
        "NPA content nodes:",
        len(content_nodes),
    )

    print(
        "NPA total nodes:",
        len(nodes),
    )

    return nodes


# =====================================================
# BUILD NPA INDEX
# =====================================================

def create_npa_vector_index():
    print(
        "\n###################################"
    )
    print(
        "# BUILD NPA EMBEDDINGS"
    )
    print(
        "###################################"
    )

    if not (
        NPA_CATALOG_FILE.exists()
    ):
        raise FileNotFoundError(
            "NPA_TABLE.xlsx "
            "не найден: "
            f"{NPA_CATALOG_FILE}"
        )

    df = pd.read_excel(
        NPA_CATALOG_FILE
    )

    validate_npa_dataframe(
        df
    )

    catalog_documents = (
        create_npa_catalog_documents(
            df
        )
    )

    content_documents = (
        create_npa_content_documents(
            df
        )
    )

    print(
        "\nNPA catalog documents:",
        len(catalog_documents),
    )

    print(
        "NPA content source parts:",
        len(content_documents),
    )

    nodes = create_npa_nodes(
        catalog_documents,
        content_documents,
    )

    return create_index_from_nodes(
        nodes=nodes,
        table_name=NPA_TABLE,
    )


# =====================================================
# METHOD DOCUMENTS
# =====================================================

METHOD_REQUIRED_COLUMNS = {
    "id",
    "Дата",
    "Форма",
    "Название",
    "ссылка",
    "input_file",
}


def validate_method_dataframe(
    df: pd.DataFrame,
) -> None:

    missing = (
        METHOD_REQUIRED_COLUMNS
        - set(df.columns)
    )

    if missing:
        raise ValueError(
            "В METHOD_TABLE.xlsx "
            "отсутствуют колонки: "
            + ", ".join(
                sorted(missing)
            )
        )

    if df["id"].isna().any():
        raise ValueError(
            "В METHOD_TABLE.xlsx "
            "есть строки с пустым id."
        )

    normalized_ids = [
        str(
            normalize_document_id(
                value
            )
        )
        for value
        in df["id"].tolist()
    ]

    if (
        len(normalized_ids)
        != len(set(normalized_ids))
    ):
        raise ValueError(
            "В METHOD_TABLE.xlsx "
            "id документов должны "
            "быть уникальными."
        )


def method_common_metadata(
    row: pd.Series,
) -> dict[str, Any]:

    method_id = str(
        normalize_document_id(
            row["id"]
        )
    )

    metadata = {
        "knowledge_type":
            "method",

        "method_id":
            method_id,

        "title":
            cell_to_text(
                row["Название"]
            ),

        "form":
            cell_to_text(
                row["Форма"]
            ),

        "date":
            cell_to_text(
                row["Дата"]
            ),

        "url":
            cell_to_text(
                row["ссылка"]
            ),

        "input_file":
            cell_to_text(
                row["input_file"]
            ),
    }

    return compact_metadata(
        metadata
    )


def create_method_catalog_documents(
    df: pd.DataFrame,
) -> list[Document]:

    documents: list[Document] = []

    for row_index, row in (
        df.iterrows()
    ):

        metadata = (
            method_common_metadata(
                row
            )
        )

        metadata.update(
            {
                "record_type":
                    "catalog",

                "source":
                    METHOD_CATALOG_FILE.name,

                "row_index":
                    int(row_index),

                "file_type":
                    "excel",
            }
        )

        text_parts = [
            (
                "Форма документа: "
                + cell_to_text(
                    row["Форма"]
                )
            ),
            (
                "Дата: "
                + cell_to_text(
                    row["Дата"]
                )
            ),
            (
                "Название: "
                + cell_to_text(
                    row["Название"]
                )
            ),
        ]

        text = "\n".join(
            value
            for value
            in text_parts
            if not value.endswith(": ")
        )

        documents.append(
            Document(
                text=text,
                metadata=metadata,
            )
        )

    return documents


def create_method_content_documents(
    df: pd.DataFrame,
) -> list[Document]:

    documents: list[Document] = []

    METHOD_DOCUMENTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for _, row in df.iterrows():

        metadata_base = (
            method_common_metadata(
                row
            )
        )

        method_id = (
            metadata_base[
                "method_id"
            ]
        )

        input_file = (
            metadata_base.get(
                "input_file",
                "",
            )
        )

        if not input_file:
            print(
                "WARNING: "
                f"METHOD id={method_id}: "
                "input_file не указан. "
                "Будет создана только "
                "catalog-запись."
            )
            continue

        file_path = Path(
            input_file
        )

        if not file_path.is_absolute():
            file_path = (
                METHOD_DOCUMENTS_DIR
                / file_path
            )

        file_path = (
            file_path.resolve()
        )

        if not file_path.exists():
            print(
                "WARNING: "
                f"METHOD id={method_id}: "
                "файл не найден: "
                f"{file_path}"
            )
            continue

        if (
            file_path.suffix.lower()
            not in SUPPORTED_NPA_EXTENSIONS
        ):
            print(
                "WARNING: "
                f"METHOD id={method_id}: "
                "неподдерживаемый формат: "
                f"{file_path.suffix}"
            )
            continue

        print(
            "\nREAD METHOD CONTENT:"
        )

        print(
            f"  id={method_id}"
        )

        print(
            f"  file={file_path.name}"
        )

        try:
            loaded_documents = (
                SimpleDirectoryReader(
                    input_files=[
                        str(file_path)
                    ],
                    raise_on_error=True,
                )
                .load_data()
            )

        except Exception as exc:
            print(
                "WARNING: "
                "не удалось прочитать "
                f"{file_path.name}: "
                f"{exc}"
            )
            continue

        added_parts = 0

        for part_index, loaded in (
            enumerate(
                loaded_documents,
                start=1,
            )
        ):

            text = (
                loaded.text
                or ""
            ).strip()

            if not text:
                continue

            metadata = dict(
                metadata_base
            )

            metadata.update(
                {
                    "record_type":
                        "content",

                    "source":
                        file_path.name,

                    "file_type":
                        file_path
                        .suffix
                        .lower()
                        .lstrip("."),

                    "content_part":
                        part_index,
                }
            )

            loaded_metadata = (
                getattr(
                    loaded,
                    "metadata",
                    {},
                )
                or {}
            )

            for key in (
                "page_label",
                "page_number",
            ):
                if (
                    key
                    not in loaded_metadata
                ):
                    continue

                value = (
                    loaded_metadata[key]
                )

                if value is not None:
                    metadata[key] = value

            documents.append(
                Document(
                    text=text,
                    metadata=(
                        compact_metadata(
                            metadata
                        )
                    ),
                )
            )

            added_parts += 1

        print(
            "  extracted parts:",
            added_parts,
        )

        if added_parts == 0:
            print(
                "WARNING: "
                f"{file_path.name} "
                "прочитан, но текст "
                "не извлечён. "
                "Возможно, это скан."
            )

    return documents


def create_method_nodes(
    catalog_documents:
        list[Document],

    content_documents:
        list[Document],
):

    nodes = []

    # -----------------------------------------
    # CATALOG
    # -----------------------------------------

    for document in (
        catalog_documents
    ):

        method_id = (
            document.metadata[
                "method_id"
            ]
        )

        node = TextNode(
            id_=(
                f"method-catalog-"
                f"{method_id}"
            ),

            text=document.text,

            metadata=(
                document.metadata
            ),
        )

        nodes.append(
            node
        )

    # -----------------------------------------
    # CONTENT
    # -----------------------------------------

    splitter = SentenceSplitter(
        chunk_size=1000,
        chunk_overlap=120,
    )

    content_nodes = (
        splitter
        .get_nodes_from_documents(
            content_documents
        )
    )

    chunk_counters: dict[
        str,
        int,
    ] = {}

    for node in content_nodes:

        method_id = (
            node.metadata.get(
                "method_id"
            )
        )

        key = str(
            method_id
        )

        chunk_index = (
            chunk_counters.get(
                key,
                0,
            )
        )

        node.metadata[
            "chunk_index"
        ] = chunk_index

        node.id_ = (
            f"method-content-"
            f"{key}-"
            f"{chunk_index}"
        )

        chunk_counters[key] = (
            chunk_index
            + 1
        )

        nodes.append(
            node
        )

    print(
        "\nMETHOD catalog nodes:",
        len(catalog_documents),
    )

    print(
        "METHOD content nodes:",
        len(content_nodes),
    )

    print(
        "METHOD total nodes:",
        len(nodes),
    )

    return nodes


def create_method_vector_index():

    print(
        "\n###################################"
    )

    print(
        "# BUILD METHOD EMBEDDINGS"
    )

    print(
        "###################################"
    )

    if not (
        METHOD_CATALOG_FILE.exists()
    ):
        raise FileNotFoundError(
            "METHOD_TABLE.xlsx "
            "не найден: "
            f"{METHOD_CATALOG_FILE}"
        )

    df = pd.read_excel(
        METHOD_CATALOG_FILE
    )

    validate_method_dataframe(
        df
    )

    catalog_documents = (
        create_method_catalog_documents(
            df
        )
    )

    content_documents = (
        create_method_content_documents(
            df
        )
    )

    print(
        "\nMETHOD catalog documents:",
        len(catalog_documents),
    )

    print(
        "METHOD content source parts:",
        len(content_documents),
    )

    nodes = (
        create_method_nodes(
            catalog_documents,
            content_documents,
        )
    )

    return create_index_from_nodes(
        nodes=nodes,
        table_name=METHOD_DOCS_TABLE,
    )

# =====================================================
# BUILD TARGETS
# =====================================================

def build_npa_index():
    create_npa_vector_index()


def build_method_index():
    create_method_vector_index()


def build_all_indexes():

    print(
        "BUILD NPA EMBEDDINGS"
    )
    create_npa_vector_index()

    print(
        "BUILD METHOD EMBEDDINGS"
    )

    create_method_vector_index()

    print(
        "\n###################################"
    )
    print(
        "# BUILD INTERNET EMBEDDINGS"
    )
    print(
        "###################################"
    )

    create_vector_index(
        files=[
            DATA_DIR
            / "INTERNET_TABLE.xlsx"
        ],
        table_name=(
            INTERNET_RESOURCES_TABLE
        ),
    )

    print(
        "\n###################################"
    )
    print(
        "# BUILD FLOOD EMBEDDINGS"
    )
    print(
        "###################################"
    )

    create_vector_index(
        files=[
            DATA_DIR
            / "Объекты_затопления.xlsx"
        ],
        table_name=(
            FLOOD_OBJECTS_TABLE
        ),
    )

    print(
        "\n###################################"
    )
    print(
        "# BUILD ADAPTATION EMBEDDINGS"
    )
    print(
        "###################################"
    )

    create_vector_index(
        files=[
            DATA_DIR
            / "Реестр_адапт_мер.xlsx",

            DATA_DIR
            / "Реестр_адапт_мер2.xlsx",

            DATA_DIR
            / "Реестр_адапт_мер3.xlsx",
        ],
        table_name=(
            ADAPTATION_TABLE
        ),
    )


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "target",
        nargs="?",
        choices=[
            "npa",
            "method",
            "all",
        ],
        default="npa",
        help=(
            "Что перестраивать: "
            "npa или all. "
            "По умолчанию npa."
        ),
    )

    args = parser.parse_args()

    initialize_embedding_model()

    if args.target == "npa":
        build_npa_index()
    elif args.target == "method":
        build_method_index()
    else:
        build_all_indexes()