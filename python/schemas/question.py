from typing import Optional
from pydantic import BaseModel


class QuestionRequest(BaseModel):
    question: str
    context: Optional[str] = None
    conversation_id: Optional[int] = None
    request_id: Optional[str] = None


class QuestionResponse(BaseModel):
    answer: str
    status: str
