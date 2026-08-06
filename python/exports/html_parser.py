from typing import TypeAlias

from bs4 import BeautifulSoup
from bs4.element import Tag


TableData: TypeAlias = list[list[str]]
ParsedTables: TypeAlias = list[TableData]


def parse_html_table(
    html: str,
) -> tuple[ParsedTables, str]:
    """
    Извлекает таблицы из HTML и текст,
    расположенный после последней таблицы.

    Возвращает:
        - список таблиц;
        - текст источников после последней таблицы.
    """
    if not html or not html.strip():
        return [], ""

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    tables = soup.find_all("table")

    result: ParsedTables = []

    for table in tables:
        table_data: TableData = []

        header = table.find("thead")

        if header:
            header_rows = header.find_all(
                "tr",
                recursive=False,
            )

            for header_row in header_rows:
                headers = [
                    cell.get_text(
                        " ",
                        strip=True,
                    )
                    for cell in header_row.find_all(
                        ["th", "td"],
                    )
                ]

                if headers and any(headers):
                    table_data.append(headers)

        tbody = table.find("tbody")

        if tbody:
            rows = tbody.find_all(
                "tr",
                recursive=False,
            )
        else:
            rows = table.find_all(
                "tr",
                recursive=False,
            )

            # В некоторых HTML строка заголовка находится
            # непосредственно внутри thead. Она уже была добавлена выше.
            if header:
                rows = [
                    row
                    for row in rows
                    if row.find_parent("thead") is None
                ]

        for row in rows:
            cells = [
                cell.get_text(
                    " ",
                    strip=True,
                )
                for cell in row.find_all(
                    ["td", "th"],
                    recursive=False,
                )
            ]

            if cells and any(cells):
                table_data.append(cells)

        if table_data:
            result.append(table_data)

    sources_text = _extract_text_after_last_table(
        soup
    )

    return result, sources_text

def _extract_text_after_last_table(
    soup: BeautifulSoup,
) -> str:
    markdown_div = (
        soup.find(class_="markdown-content")
        or soup
    )

    all_tables = markdown_div.find_all("table")

    if not all_tables:
        return ""

    last_table = all_tables[-1]

    after_parts: list[str] = []
    found_last_table = False

    for element in markdown_div.find_all(
        string=True,
    ):
        parent = element.parent

        if not isinstance(parent, Tag):
            continue

        if (
            parent == last_table
            or parent.find_parent("table")
            == last_table
        ):
            found_last_table = True
            continue

        if not found_last_table:
            continue

        # Не добавляем текст из других таблиц,
        # если после последней целевой таблицы
        # встречается вложенная HTML-разметка.
        if parent.find_parent("table") is not None:
            continue

        text = element.strip()

        if text:
            after_parts.append(text)

    unique_lines: list[str] = []
    seen: set[str] = set()

    for line in after_parts:
        line_clean = line.strip()

        if (
            line_clean
            and line_clean not in seen
        ):
            seen.add(line_clean)
            unique_lines.append(line_clean)

    return "\n".join(unique_lines).strip()
