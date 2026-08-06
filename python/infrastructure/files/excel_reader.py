import logging
import os

import pandas as pd
from llama_index.core import Document


logger = logging.getLogger(__name__)


EMBED_COLUMNS = [
    "Проблема",
    "Наименование мероприятий",
    "Митигационный эффект",
    "Адаптационный эффект",
]

META_COLUMNS = [
    "Наименование района",
    "Агроклиматические условия района",
    "Ответственная организация",
    "Источник",
]


def read_excel_as_documents(
    file_path: str,
) -> list[Document]:
    dataframe = pd.read_excel(file_path)
    documents: list[Document] = []

    for row_index, row in dataframe.iterrows():
        embed_text_parts: list[str] = []

        for column in EMBED_COLUMNS:
            if (
                column in dataframe.columns
                and pd.notna(row[column])
            ):
                embed_text_parts.append(
                    f"{column}: {row[column]}"
                )

        embed_text = "\n".join(embed_text_parts)

        metadata = {
            "source": os.path.basename(file_path),
            "row_index": int(row_index),
            "file_type": "excel",
        }

        for column in META_COLUMNS:
            if (
                column in dataframe.columns
                and pd.notna(row[column])
            ):
                metadata[f"meta_{column}"] = str(
                    row[column]
                )

        if embed_text.strip():
            documents.append(
                Document(
                    text=embed_text,
                    metadata=metadata,
                )
            )

    return documents


def process_excel_files(
    data_path: str,
) -> list[Document]:
    all_documents: list[Document] = []

    if not os.path.isdir(data_path):
        logger.warning(
            "Директория с Excel-файлами не найдена: %s",
            data_path,
        )
        return all_documents

    for file_name in sorted(os.listdir(data_path)):
        if not file_name.lower().endswith(
            (".xlsx", ".xls")
        ):
            continue

        file_path = os.path.join(
            data_path,
            file_name,
        )

        if not os.path.isfile(file_path):
            continue

        logger.info(
            "Обработка Excel-файла: %s",
            file_name,
        )

        try:
            excel_documents = read_excel_as_documents(
                file_path
            )
            all_documents.extend(excel_documents)

            logger.info(
                "Из файла %s получено документов: %s",
                file_name,
                len(excel_documents),
            )

        except Exception:
            logger.exception(
                "Ошибка обработки Excel-файла: %s",
                file_name,
            )

    return all_documents
