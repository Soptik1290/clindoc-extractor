from pydantic import BaseModel, Field
from typing import Literal

class ExtractionRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Lékařský diktát")
    language: Literal["cs", "en", "auto"] = Field(
        default="auto",
        description="Jazyk textu"
    )

class SubmitRequest(ExtractionRequest):
    pass
