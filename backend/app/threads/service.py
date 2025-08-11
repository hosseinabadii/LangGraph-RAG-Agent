from collections.abc import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from langgraph.checkpoint.base import BaseCheckpointSaver
from loguru import logger
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Thread
from app.db.pgvector_utils import delete_document_from_pgvector, search_documents_in_pgvector

from .schemas import ThreadUpdate


async def create_new_thread(user_id: UUID, session: AsyncSession) -> Thread:
    new_thread = Thread()
    new_thread.user_id = user_id
    session.add(new_thread)
    await session.commit()
    return new_thread


async def get_user_threads(user_id: UUID, session: AsyncSession) -> Sequence[Thread]:
    statement = select(Thread).where(Thread.user_id == user_id).order_by(desc(Thread.created_at))
    result = await session.execute(statement)
    return result.scalars().all()


async def get_thread(thread_id: UUID, user_id: UUID, session: AsyncSession) -> Thread:
    db_thread = await session.get(Thread, thread_id)
    if db_thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread with ID {thread_id} not found.",
        )
    if db_thread.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to get this thread.",
        )
    return db_thread


async def update_thread(thread_data: ThreadUpdate, thread_id: UUID, user_id: UUID, session: AsyncSession) -> Thread:
    db_thread = await session.get(Thread, thread_id)
    if db_thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread with ID {thread_id} not found.",
        )
    if db_thread.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this thread.",
        )
    db_thread.title = thread_data.title
    await session.commit()
    await session.refresh(db_thread)
    return db_thread


async def delete_thread(
    thread_id: UUID, user_id: UUID, session: AsyncSession, checkpointer: BaseCheckpointSaver
) -> None:
    db_thread = await session.get(Thread, thread_id)
    if db_thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread with ID {thread_id} not found.",
        )
    if db_thread.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this thread.",
        )
    await session.delete(db_thread)
    await session.commit()

    try:
        logger.info(f"Attempting to delete thread {thread_id} from checkpointer (chat messages)")
        await checkpointer.adelete_thread(thread_id=str(thread_id))
        logger.info(f"Successfully deleted thread {thread_id} from checkpointer (chat messages)")
    except Exception as e:
        logger.error(f"Failed to delete thread {thread_id} from checkpointer (chat messages): {str(e)}")

    try:
        logger.info(f"Attempting to delete documents related to thread_id {thread_id}")
        document_chunks = await search_documents_in_pgvector(filter={"thread_id": str(thread_id)})
        if not document_chunks:
            logger.warning(f"Document chunks related to thread {thread_id} not found in PGVector.")
        else:
            doc_ids_to_delete = [doc.metadata["id"] for doc in document_chunks]
            await delete_document_from_pgvector(doc_ids_to_delete)
            logger.info(f"Successfully deleted all document chunks related to thread_id: {thread_id} from PGVector.")
    except Exception as e:
        logger.error(f"Failed to delete documents related to thread {thread_id} from PGVector: {str(e)}")
