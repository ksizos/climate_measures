from __future__ import annotations

import re
from calendar import monthrange
from datetime import date


MONTHS = {
    # именительный падеж
    "январь": 1,
    "февраль": 2,
    "март": 3,
    "апрель": 4,
    "май": 5,
    "июнь": 6,
    "июль": 7,
    "август": 8,
    "сентябрь": 9,
    "октябрь": 10,
    "ноябрь": 11,
    "декабрь": 12,

    # родительный падеж — для "на 1 января"
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}


ROMAN_QUARTERS = {
    "i": 1,
    "ii": 2,
    "iii": 3,
    "iv": 4,
}


def normalize_period_label(
    period_label: str,
) -> str:
    """
    Нормализует текст периода только для распознавания.

    Название, которое хранится в БД, менять не обязательно.
    """

    text = str(period_label)

    text = (
        text
        .replace("\xa0", " ")
        .replace("–", "-")
        .replace("—", "-")
        .replace("−", "-")
        .replace("-", "-")
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return (
        text
        .strip()
        .lower()
        .replace("ё", "е")
    )


def last_day_of_month(
    year: int,
    month: int,
) -> int:
    return monthrange(
        year,
        month,
    )[1]


def period_dates(
    period_label: str,
    year: int,
) -> tuple[date, date]:
    """
    Возвращает start_date и end_date для периода из Excel.

    При неизвестном формате не оставляет NULL молча,
    а выбрасывает исключение.
    """

    label = normalize_period_label(
        period_label
    )

    # ---------------------------------------------------------
    # Год
    # ---------------------------------------------------------

    if label in {
        "год",
        "за год",
    }:
        return (
            date(year, 1, 1),
            date(year, 12, 31),
        )

    # ---------------------------------------------------------
    # На конец года — момент времени
    # ---------------------------------------------------------

    if label == "на конец года":
        point = date(
            year,
            12,
            31,
        )

        return point, point

    # ---------------------------------------------------------
    # Конкретная дата:
    # "на 1 января"
    # "на 15 мая"
    # ---------------------------------------------------------

    match = re.fullmatch(
        r"на\s+(\d{1,2})\s+([а-я]+)",
        label,
    )

    if match:
        day = int(
            match.group(1)
        )

        month_name = (
            match.group(2)
        )

        month = MONTHS.get(
            month_name
        )

        if month is None:
            raise ValueError(
                "Неизвестный месяц "
                f"в периоде: {period_label}"
            )

        point = date(
            year,
            month,
            day,
        )

        return point, point

    # ---------------------------------------------------------
    # Диапазон месяцев:
    # "январь-март"
    # "январь-июнь"
    # "апрель-июнь" и т.д.
    # ---------------------------------------------------------

    match = re.fullmatch(
        r"([а-я]+)-([а-я]+)",
        label,
    )

    if match:
        start_month_name = (
            match.group(1)
        )
        end_month_name = (
            match.group(2)
        )

        start_month = MONTHS.get(
            start_month_name
        )
        end_month = MONTHS.get(
            end_month_name
        )

        if (
            start_month is None
            or end_month is None
        ):
            raise ValueError(
                "Не удалось распознать "
                f"месяцы: {period_label}"
            )

        if start_month > end_month:
            raise ValueError(
                "Диапазон месяцев переходит "
                "через границу года: "
                f"{period_label}"
            )

        return (
            date(
                year,
                start_month,
                1,
            ),
            date(
                year,
                end_month,
                last_day_of_month(
                    year,
                    end_month,
                ),
            ),
        )

    # ---------------------------------------------------------
    # Кварталы:
    # I квартал
    # 1 квартал
    # ---------------------------------------------------------

    match = re.fullmatch(
        r"([ivx]+|\d+)\s+квартал",
        label,
    )

    if match:
        quarter_raw = (
            match.group(1)
        )

        if quarter_raw.isdigit():
            quarter = int(
                quarter_raw
            )
        else:
            quarter = (
                ROMAN_QUARTERS
                .get(quarter_raw)
            )

        if quarter not in {
            1,
            2,
            3,
            4,
        }:
            raise ValueError(
                "Некорректный квартал: "
                f"{period_label}"
            )

        start_month = (
            (quarter - 1) * 3 + 1
        )

        end_month = (
            start_month + 2
        )

        return (
            date(
                year,
                start_month,
                1,
            ),
            date(
                year,
                end_month,
                last_day_of_month(
                    year,
                    end_month,
                ),
            ),
        )

    # ---------------------------------------------------------
    # Накопительный период:
    # "за 3 месяца"
    # "за 6 месяцев"
    # "за 9 месяцев"
    # ---------------------------------------------------------

    match = re.fullmatch(
        r"за\s+(\d{1,2})\s+месяц(?:а|ев)?",
        label,
    )

    if match:
        months_count = int(
            match.group(1)
        )

        if not 1 <= months_count <= 12:
            raise ValueError(
                "Некорректное количество "
                f"месяцев: {period_label}"
            )

        return (
            date(
                year,
                1,
                1,
            ),
            date(
                year,
                months_count,
                last_day_of_month(
                    year,
                    months_count,
                ),
            ),
        )

    raise ValueError(
        "Неизвестный формат периода: "
        f"{period_label!r}"
    )