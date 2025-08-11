from collections.abc import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document

from .schemas import DocumetCreate


async def get_documents(thread_id: UUID, session: AsyncSession) -> Sequence[Document]:
    statement = select(Document).where(Document.thread_id == thread_id)
    result = await session.execute(statement)
    return result.scalars().all()


async def insert_document(document_data: DocumetCreate, session: AsyncSession) -> Document:
    new_document = Document(**document_data.model_dump())
    session.add(new_document)
    await session.commit()
    return new_document


async def delete_document(document_id: UUID, session: AsyncSession) -> None:
    db_document = await session.get(Document, document_id)
    if db_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found.",
        )
    await session.delete(db_document)
    await session.commit()
