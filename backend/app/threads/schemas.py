from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ThreadUpdate(BaseModel):
    title: str = Field(max_length=255)


class ThreadPublic(BaseModel):
    id: UUID
    title: str
    user_id: UUID
    created_at: datetime
