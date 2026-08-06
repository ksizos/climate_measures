from pydantic import BaseModel

class RebuildResult(BaseModel):
    success: bool
    documents_count: int = 0
    message: str
