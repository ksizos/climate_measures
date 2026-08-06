import os
from functools import lru_cache

import pandas as pd

from core.config import (
    INTERNET_RESOURCES_TABLE,
    METHOD_DOCS_TABLE,
    NPA_TABLE,
)

def _excel_file_to_text_context(
    file_path: str,
    title: str,
) -> str:
    if not os.path.isfile(file_path):
        return (
            f"{title}: файл не найден: "
            f"{file_path}"
        )

    parts = [f"{title}:"]

    try:
        excel_file = pd.ExcelFile(file_path)

        for sheet_name in excel_file.sheet_names:
            dataframe = pd.read_excel(
                excel_file,
                sheet_name=sheet_name,
            ).fillna("")

            lines: list[str] = []

            for _, row in dataframe.iterrows():
                row_dict = {
                    str(column).strip(): str(value).strip()
                    for column, value in row.to_dict().items()
                    if str(value).strip()
                }

                line = " | ".join(
                    f"{column}: {value}"
                    for column, value in row_dict.items()
                )

                if line:
                    lines.append(line)

            if lines:
                sheet_text = "\n".join(
                    f"- {line}"
                    for line in lines
                )

                parts.append(
                    f"Лист: {sheet_name}\n"
                    f"{sheet_text}"
                )

    except Exception as error:
        return (
            f"Ошибка чтения файла "
            f"{file_path}: {error}"
        )

    return "\n\n".join(parts)


@lru_cache(maxsize=1)
def load_npa_context() -> str:
    return _excel_file_to_text_context(
        NPA_TABLE,
        "Нормативно-правовые акты из локальной базы",
    )


@lru_cache(maxsize=1)
def load_method_docs_context() -> str:
    return _excel_file_to_text_context(
        METHOD_DOCS_TABLE,
        (
            "Методические и аналитические документы "
            "из локальной базы"
        ),
    )


@lru_cache(maxsize=1)
def load_internet_resources_context() -> str:
    return _excel_file_to_text_context(
        INTERNET_RESOURCES_TABLE,
        "Интернет-ресурсы из локальной базы",
    )
