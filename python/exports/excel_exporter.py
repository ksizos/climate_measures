import re

from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet


def add_sources_to_excel(
    worksheet: Worksheet,
    sources_text: str | None,
    start_row: int,
) -> int:
    """
    Добавляет блок опорных источников в Excel-лист.

    Возвращает номер следующей свободной строки.
    """
    if not sources_text or not sources_text.strip():
        return start_row

    lines = sources_text.strip().splitlines()
    header_added = False

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            continue

        if (
            "опорные источники" in line.lower()
            and not header_added
        ):
            header_cell = worksheet.cell(
                row=start_row,
                column=1,
                value="Опорные источники:",
            )
            header_cell.font = Font(bold=True)

            start_row += 1
            header_added = True

            line = re.sub(
                r"опорные источники[:\s]*",
                "",
                line,
                flags=re.IGNORECASE,
            ).strip()

            if not line:
                continue

        cell = worksheet.cell(
            row=start_row,
            column=1,
            value=line,
        )

        url_match = re.search(
            r"https?://[^\s\]\[•\n]+",
            line,
        )

        if url_match:
            url = url_match.group(0)

            try:
                cell.hyperlink = url
                cell.style = "Hyperlink"
            except (TypeError, ValueError):
                # Текст источника останется в ячейке,
                # даже если hyperlink применить не удалось.
                pass

        start_row += 1

    return start_row
