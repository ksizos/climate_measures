from pydantic import BaseModel

class ApprovedMeasure(BaseModel):
    name: str
    mitigation: str | None = None
    adaptation: str
    relevance: str
    responsible: str
    source_question: str | None = None
    source_url: str | None = None
