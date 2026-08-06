import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.core.vector_stores.types import BasePydanticVectorStore

from infrastructure.llm.embeddings import embed_model
from infrastructure.files.excel_reader import (
    process_excel_files,
)
from schemas.index import RebuildResult


logger = logging.getLogger(__name__)


class VectorIndexRebuilder:
    def __init__(
        self,
        vector_store_factory: Callable[
            [],
            BasePydanticVectorStore,
        ],
        approved_measure_repository: Any,
        data_directory: str | Path,
    ) -> None:
        self._vector_store_factory = (
            vector_store_factory
        )
        self._approved_measure_repository = (
            approved_measure_repository
        )
        self._data_directory = Path(
            data_directory
        )

    def rebuild(self) -> RebuildResult:
        logger.info(
            "Начато перестроение векторного индекса"
        )

        try:
            documents = process_excel_files(
                str(self._data_directory)
            )

            approved_documents = (
                self._load_approved_measure_documents()
            )
            documents.extend(approved_documents)

            if not documents:
                return RebuildResult(
                    success=False,
                    documents_count=0,
                    message=(
                        "Документы для построения "
                        "индекса не найдены"
                    ),
                )

            vector_store = (
                self._vector_store_factory()
            )

            storage_context = (
                StorageContext.from_defaults(
                    vector_store=vector_store,
                )
            )

            VectorStoreIndex.from_documents(
                documents=documents,
                storage_context=storage_context,
                embed_model=embed_model,
                show_progress=True,
            )

            logger.info(
                "Векторный индекс перестроен. "
                "Количество документов: %s",
                len(documents),
            )

            return RebuildResult(
                success=True,
                documents_count=len(documents),
                message=(
                    "Векторный индекс успешно "
                    "перестроен"
                ),
            )

        except Exception as error:
            logger.exception(
                "Ошибка перестроения "
                "векторного индекса"
            )

            return RebuildResult(
                success=False,
                documents_count=0,
                message=(
                    "Ошибка перестроения индекса: "
                    f"{error}"
                ),
            )

    def _load_approved_measure_documents(
        self,
    ) -> list[Document]:
        if (
            self._approved_measure_repository
            is None
        ):
            return []

        get_measures = getattr(
            self._approved_measure_repository,
            "get_approved_measures",
            None,
        )

        if get_measures is None:
            logger.warning(
                "Репозиторий одобренных мероприятий "
                "не содержит get_approved_measures()"
            )
            return []

        measures = get_measures()
        documents: list[Document] = []

        for measure_index, measure in enumerate(
            measures
        ):
            if isinstance(measure, str):
                text = measure.strip()
                metadata = {
                    "source": "approved_measures",
                    "row_index": measure_index,
                    "file_type": "approved_measure",
                }
            elif isinstance(measure, dict):
                text = self._measure_to_text(measure)
                metadata = {
                    "source": "approved_measures",
                    "row_index": measure_index,
                    "file_type": "approved_measure",
                }

                for key, value in measure.items():
                    if value is not None:
                        metadata[
                            f"meta_{key}"
                        ] = str(value)
            else:
                text = str(measure).strip()
                metadata = {
                    "source": "approved_measures",
                    "row_index": measure_index,
                    "file_type": "approved_measure",
                }

            if text:
                documents.append(
                    Document(
                        text=text,
                        metadata=metadata,
                    )
                )

        return documents

    @staticmethod
    def _measure_to_text(
        measure: dict[str, Any],
    ) -> str:
        return "\n".join(
            f"{key}: {value}"
            for key, value in measure.items()
            if value is not None
            and str(value).strip()
        )
