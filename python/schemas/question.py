from pydantic import BaseModel
from typing import Optional

class QuestionRequest(BaseModel):
    question: str
    context: Optional[str] = None
    conversation_id: Optional[int] = None


class QuestionResponse(BaseModel):
    answer: str
    status: str
