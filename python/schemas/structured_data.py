from pydantic import BaseModel

class StructuredDataRequest(BaseModel):
    prompt: str
