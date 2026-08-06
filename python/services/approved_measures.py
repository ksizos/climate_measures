from llama_index.core import Document

from services.measure_service import (
    get_approved_measures,
)

def get_approved_documents() -> list[Document]:
    documents: list[Document] = []
    approved_measures = get_approved_measures()

    for row_index, item in enumerate(
        approved_measures
    ):
        embed_text = "\n".join(
            [
                (
                    "Проблема: "
                    f"{item.get('source_question', '')}"
                ),
                (
                    "Наименование мероприятий: "
                    f"{item.get('name', '')}"
                ),
                (
                    "Митигационный эффект: "
                    f"{item.get('mitigation', '')}"
                ),
                (
                    "Адаптационный эффект: "
                    f"{item.get('adaptation', '')}"
                ),
            ]
        )

        metadata = {
            "source": "user_approved_in_memory",
            "row_index": row_index,
            "file_type": "user_approved",
            "meta_Наименование района": item.get(
                "relevance",
                "",
            ),
            "meta_Ответственная организация": item.get(
                "responsible",
                "",
            ),
            "meta_Источник": item.get(
                "source_url",
                "",
            ),
        }

        documents.append(
            Document(
                text=embed_text,
                metadata=metadata,
            )
        )

    return documents
