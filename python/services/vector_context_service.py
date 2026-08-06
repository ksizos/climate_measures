from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from infrastructure.vector_store.pgvector import (
    load_vector_index,
)

logger = logging.getLogger(__name__)

LOCAL_SOURCE_URL_KEYS = (
    "url",
    "source_url",
    "meta_Источник",
    "Источник",
)

# Возможные названия документа в metadata.
LOCAL_SOURCE_TITLE_KEYS = (
    "title",
    "name",
    "document_name",
    "doc_name",
    "meta_Название",
    "Название",
    "source",
)


@dataclass(slots=True)
class RetrievedVectorDocument:
    """
    Один документ, извлечённый из PGVector.
    """

    text: str
    score: float | None

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )


@dataclass(slots=True)
class LocalSource:
    """
    Точный источник из metadata локального документа.
    """

    title: str
    url: str


@dataclass(slots=True)
class VectorContextResult:
    """
    Результат поиска по одной PGVector-таблице.
    """

    table_name: str
    query: str

    documents: list[
        RetrievedVectorDocument
    ] = field(default_factory=list)

    @property
    def found(self) -> bool:
        """
        Найден ли хотя бы один документ.
        """

        return bool(self.documents)

    def to_context(self) -> str:
        """
        Формирует контекст для NVIDIA.

        URL намеренно не передаются модели.
        Точные ссылки добавляются позже функцией
        append_exact_local_sources().
        """

        if not self.documents:
            return (
                "В локальной векторной базе "
                "релевантные документы не найдены."
            )

        parts = [
            "Контекст из локальной векторной базы:"
        ]

        for index, document in enumerate(
            self.documents,
            start=1,
        ):
            block = [
                f"[LOCAL-{index}]",
                document.text.strip(),
            ]

            metadata_lines = (
                _format_metadata_for_context(
                    document.metadata
                )
            )

            if metadata_lines:
                block.extend(metadata_lines)

            if document.score is not None:
                block.append(
                    "Оценка релевантности: "
                    f"{document.score:.4f}"
                )

            parts.append(
                "\n".join(block)
            )

        return "\n\n---\n\n".join(parts)

    def get_sources(self) -> list[LocalSource]:
        """
        Извлекает точные URL из metadata документов.
        """

        result: list[LocalSource] = []
        seen_urls: set[str] = set()

        for document in self.documents:
            url = _first_metadata_value(
                document.metadata,
                LOCAL_SOURCE_URL_KEYS,
            )

            if not url:
                continue

            normalized_url = url.strip()

            if not normalized_url:
                continue

            if normalized_url in seen_urls:
                continue

            title = _first_metadata_value(
                document.metadata,
                LOCAL_SOURCE_TITLE_KEYS,
            )

            if not title:
                title = "Локальный источник"

            seen_urls.add(normalized_url)

            result.append(
                LocalSource(
                    title=title,
                    url=normalized_url,
                )
            )

        return result


def _first_metadata_value(
    metadata: dict[str, Any],
    keys: tuple[str, ...],
) -> str:
    """
    Возвращает первое непустое поле metadata
    из переданного списка ключей.
    """

    for key in keys:
        value = metadata.get(key)

        if value is None:
            continue

        text = str(value).strip()

        if text:
            return text

    return ""


def _format_metadata_for_context(
    metadata: dict[str, Any],
) -> list[str]:
    """
    Форматирует полезные metadata для NVIDIA.

    URL и внутренние служебные поля исключаются.
    """

    excluded_keys = {
        *LOCAL_SOURCE_URL_KEYS,
        "_node_content",
        "_node_type",
        "document_id",
        "doc_id",
        "ref_doc_id",
    }

    lines: list[str] = []

    for key, value in metadata.items():
        if key in excluded_keys:
            continue

        if value is None:
            continue

        text = str(value).strip()

        if not text:
            continue

        display_name = (
            str(key)
            .removeprefix("meta_")
            .replace("_", " ")
        )

        lines.append(
            f"{display_name}: {text}"
        )

    return lines


def retrieve_vector_context(
    query: str,
    *,
    table_name: str,
    top_k: int = 4,
    min_score: float | None = None,
) -> VectorContextResult:
    """
    Выполняет semantic search в конкретной
    PGVector-таблице.

    Примеры table_name:
    - NPA_TABLE;
    - METHOD_DOCS_TABLE;
    - INTERNET_RESOURCES_TABLE.
    """

    clean_query = query.strip()

    if not clean_query:
        raise ValueError(
            "Векторный запрос не может быть пустым."
        )

    if not table_name or not table_name.strip():
        raise ValueError(
            "Не указано имя PGVector-таблицы."
        )

    if top_k <= 0:
        raise ValueError(
            "top_k должен быть больше нуля."
        )

    logger.info(
        "Vector retrieval START: "
        "table=%s, top_k=%s, min_score=%s, query=%s",
        table_name,
        top_k,
        min_score,
        clean_query[:300],
    )

    index = load_vector_index(
        table_name=table_name,
    )

    retriever = index.as_retriever(
        similarity_top_k=top_k,
    )

    nodes = retriever.retrieve(
        clean_query
    )

    documents: list[
        RetrievedVectorDocument
    ] = []

    for node in nodes:
        text = node.get_content().strip()

        if not text:
            continue

        raw_score = getattr(
            node,
            "score",
            None,
        )

        score = (
            float(raw_score)
            if raw_score is not None
            else None
        )

        if (
            min_score is not None
            and score is not None
            and score < min_score
        ):
            continue

        metadata = dict(
            getattr(
                node,
                "metadata",
                {},
            )
            or {}
        )

        documents.append(
            RetrievedVectorDocument(
                text=text,
                score=score,
                metadata=metadata,
            )
        )

    logger.info(
        "Vector retrieval FINISHED: "
        "table=%s, documents=%s",
        table_name,
        len(documents),
    )

    return VectorContextResult(
        table_name=table_name,
        query=clean_query,
        documents=documents,
    )


def append_exact_local_sources(
    answer: str,
    result: VectorContextResult,
) -> str:
    """
    Программно добавляет точные URL локальных
    документов после генерации NVIDIA.

    Благодаря этому модель не может изменить символы
    внутри ссылки.
    """

    sources = result.get_sources()

    if not sources:
        return answer.strip()

    lines = [
        answer.strip(),
        "",
        "### Источники локальной базы",
    ]

    for index, source in enumerate(
        sources,
        start=1,
    ):
        lines.append(
            f"{index}. {source.title}\n"
            f"   {source.url}"
        )

    return "\n".join(lines)
