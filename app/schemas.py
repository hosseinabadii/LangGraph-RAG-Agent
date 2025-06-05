from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class ModelOptions(StrEnum):
    OPENAI_GPT_4O_MINI = "openai/gpt-4o-mini"
    OPENAI_GPT_4O = "openai/gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"


class PromptInput(BaseModel):
    question: str
    model: ModelOptions = Field(default=ModelOptions.OPENAI_GPT_4O_MINI)
    session_id: UUID | None = Field(default=None)


class DocumentMetadata(BaseModel):
    title: str = Field(default="Not Available")
    page_label: str = Field(default="Not Available")
    file_id: int | None = Field(default=None)


class PromptResponse(BaseModel):
    answer: str
    metadata: list[DocumentMetadata]
    model: ModelOptions
    session_id: UUID


class DocumentInfo(BaseModel):
    id: int
    file_name: str
    uploaded_at: datetime


class DocumentUploadResponse(BaseModel):
    file_id: int
    message: str


class DocumentDeleteResponse(BaseModel):
    message: str
