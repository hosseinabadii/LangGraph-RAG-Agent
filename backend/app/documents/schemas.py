from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumetCreate(BaseModel):
    file_name: str = Field(max_length=255)
    thread_id: UUID


class DocumentPublic(BaseModel):
    id: UUID
    file_name: str
    thread_id: UUID
    uploaded_at: datetime


class DocumentUploadResponse(BaseModel):
    document_id: UUID
    message: str


class DocumentDeleteResponse(BaseModel):
    message: str
