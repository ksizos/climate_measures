from schemas.measure import ApprovedMeasure

APPROVED_MEASURES: list[dict[str, object]] = []

def add_approved_measure(
    measure: ApprovedMeasure,
) -> None:
    APPROVED_MEASURES.append(
        measure.model_dump()
    )

def get_approved_measures() -> list[dict[str, object]]:
    return APPROVED_MEASURES
