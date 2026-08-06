from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        description="HTML-содержимое с таблицами",
    )
    filename: str = Field(
        default="export",
        min_length=1,
        description="Имя экспортируемого файла",
    )
