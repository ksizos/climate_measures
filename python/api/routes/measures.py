import threading

from fastapi import APIRouter, HTTPException

from schemas.measure import ApprovedMeasure
from services.index_rebuild_service import background_rebuild_index
from services.measure_service import add_approved_measure

router = APIRouter(
    tags=["measures"],
)

@router.post("/approve-measure")
async def approve_measure(
    measure: ApprovedMeasure,
) -> dict[str, object]:
    try:
        add_approved_measure(measure)

        print(f"✅ Одобрено мероприятие: {measure.name}")

        threading.Thread(
            target=background_rebuild_index,
            name="approved-measure-index-rebuild",
            daemon=True,
        ).start()

        return {
            "success": True,
            "message": "Добавлено. Ребилд запущен в фоне.",
        }

    except Exception as exc:
        print(f"Ошибка /approve-measure: {exc}")
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc
