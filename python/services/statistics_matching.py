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
    top_k: int = 30,
) -> tuple[pd.DataFrame, pd.DataFrame]:
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

    indicators_df = (
        get_indicators_for_territories(
            matched_territory_names
        ).copy()
    )

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

    def score_row(row: pd.Series) -> float:
        candidate = " | ".join(
            [
                str(row.get("indicator_name", "")),
                str(row.get("section_name", "")),
                str(row.get("unit_name", "")),
                str(row.get("industry_name", "")),
            ]
        )

        return float(
            fuzz.token_sort_ratio(
                user_question.lower(),
                candidate.lower(),
            )
        )

    indicators_df["similarity"] = (
        indicators_df.apply(
            score_row,
            axis=1,
        )
    )

    top_df = (
        indicators_df
        .sort_values(
            "similarity",
            ascending=False,
        )
        .head(top_k)
        .reset_index(drop=True)
    )

    return matched_territories_df, top_df
