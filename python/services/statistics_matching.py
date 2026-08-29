import pandas as pd
from rapidfuzz import fuzz

from infrastructure.database.statistics_repository import (
    get_indicators_for_territories,
    get_statistics_metadata,
)

from services.statistics_cache import (
    statistics_cache_key,
)

def get_top_similar_territories(
    user_question: str,
    top_k: int = 2,
    min_score: float = 70.0,
) -> pd.DataFrame:
    metadata = get_statistics_metadata(
        statistics_cache_key()
    )
    territories_df = metadata[
        "territories"
    ].copy()

    if territories_df.empty:
        return territories_df

    def score_row(row: pd.Series) -> float:
        territory_name = str(
            row.get("territory_name", "")
        )

        return float(
            fuzz.partial_ratio(
                user_question.lower(),
                territory_name.lower(),
            )
        )

    territories_df["similarity"] = (
        territories_df.apply(
            score_row,
            axis=1,
        )
    )

    top_df = (
        territories_df
        .sort_values(
            "similarity",
            ascending=False,
        )
        .head(top_k)
        .reset_index(drop=True)
    )

    return (
        top_df[
            top_df["similarity"] >= min_score
        ]
        .reset_index(drop=True)
    )


def get_top_similar_indicators(
    user_question: str,
    indicator_queries: list[str],
    date_from: str | None = None,
    date_to: str | None = None,
    top_k_per_query: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame]:

    # --------------------------------------------------
    # 1. Ищем территорию как раньше
    # --------------------------------------------------

    matched_territories_df = (
        get_top_similar_territories(
            user_question
        )
    )

    matched_territory_names = (
        matched_territories_df[
            "territory_name"
        ]
        .dropna()
        .astype(str)
        .tolist()
    )

    # --------------------------------------------------
    # 2. Получаем только показатели,
    # реально имеющие статистику
    # для территории / периода
    # --------------------------------------------------

    indicators_df = (
        get_indicators_for_territories(
            territory_names=(
                matched_territory_names
            ),
            date_from=date_from,
            date_to=date_to,
        ).copy()
    )

    # Если фильтрация ничего не нашла,
    # можно сделать fallback на общие метаданные.
    if indicators_df.empty:
        metadata = get_statistics_metadata(
            statistics_cache_key()
        )

        indicators_df = metadata[
            "indicators"
        ].copy()

    if indicators_df.empty:
        return (
            matched_territories_df,
            indicators_df,
        )

    # --------------------------------------------------
    # 3. Для каждой смысловой query
    # отдельно находим TOP кандидатов
    # --------------------------------------------------

    result_frames: list[
        pd.DataFrame
    ] = []

    for indicator_query in (
        indicator_queries
    ):
        query = (
            str(indicator_query)
            .strip()
            .lower()
        )

        if not query:
            continue

        scored_df = (
            indicators_df.copy()
        )

        def score_row(
            row: pd.Series,
        ) -> float:
            indicator_name = str(
                row.get(
                    "indicator_name",
                    "",
                )
            ).lower()

            # Основной вес — название
            # самого показателя.
            name_score = max(
                fuzz.WRatio(
                    query,
                    indicator_name,
                ),
                fuzz.token_set_ratio(
                    query,
                    indicator_name,
                ),
            )

            # Дополнительный контекст.
            context = " | ".join(
                [
                    indicator_name,
                    str(
                        row.get(
                            "section_name",
                            "",
                        )
                    ).lower(),
                    str(
                        row.get(
                            "industry_name",
                            "",
                        )
                    ).lower(),
                ]
            )

            context_score = (
                fuzz.token_set_ratio(
                    query,
                    context,
                )
            )

            # Название показателя важнее
            # дополнительного контекста.
            return float(
                0.8 * name_score
                + 0.2 * context_score
            )

        scored_df[
            "similarity"
        ] = scored_df.apply(
            score_row,
            axis=1,
        )

        scored_df[
            "matched_query"
        ] = indicator_query

        top_for_query = (
            scored_df
            .sort_values(
                "similarity",
                ascending=False,
            )
            .head(
                top_k_per_query
            )
        )

        result_frames.append(
            top_for_query
        )

    if not result_frames:
        return (
            matched_territories_df,
            pd.DataFrame(),
        )

    # --------------------------------------------------
    # 4. Объединяем результаты разных
    # смысловых запросов
    # --------------------------------------------------

    result_df = pd.concat(
        result_frames,
        ignore_index=True,
    )

    # Один indicator может попасть
    # сразу в несколько query.
    #
    # Оставляем его лучший score.
    result_df = (
        result_df
        .sort_values(
            "similarity",
            ascending=False,
        )
        .drop_duplicates(
            subset=[
                "indicator_id"
            ],
            keep="first",
        )
        .reset_index(
            drop=True
        )
    )

    return (
        matched_territories_df,
        result_df,
    )

    return matched_territories_df, top_df
