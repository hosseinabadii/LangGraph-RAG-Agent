import shutil
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, status
from loguru import logger

from app.auth.dependencies import CurrentUserDep
from app.config import BASE_DIR
from app.db.main import SessionDep
from app.db.pgvector_utils import (
    DOCUMENT_LOADER_MAPPING,
    delete_document_from_pgvector,
    index_document_to_pgvector,
    search_documents_in_pgvector,
)

from . import service as document_service
from .schemas import DocumentDeleteResponse, DocumentPublic, DocumentUploadResponse, DocumetCreate

document_router = APIRouter()


@document_router.get("/{thread_id}", response_model=list[DocumentPublic])
async def get_documents(thread_id: UUID, current_user: CurrentUserDep, session: SessionDep):
    return await document_service.get_documents(thread_id, session)


@document_router.post("/upload/{thread_id}", response_model=DocumentUploadResponse)
async def upload_document(thread_id: UUID, file: UploadFile, current_user: CurrentUserDep, session: SessionDep):
    user_id = current_user.id
    if file.filename is None:
        logger.error("No file uploaded.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file uploaded.")

    allowd_extensions = list(DOCUMENT_LOADER_MAPPING.keys())
    message = f"Unsupported file type. Allowed types: {', '.join(allowd_extensions)}"
    if Path(file.filename).suffix not in allowd_extensions:
        logger.error(message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    TEMP_DIR = BASE_DIR / "tmp"
    if not TEMP_DIR.exists():
        TEMP_DIR.mkdir()
    temp_file_path = TEMP_DIR / file.filename
    document_id = None
    chunk_ids = []
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"File '{file.filename}' saved temporarily to '{temp_file_path}'.")
        document_data = DocumetCreate(file_name=file.filename, thread_id=thread_id)
        new_document = await document_service.insert_document(document_data, session)
        document_id = new_document.id
        chunk_ids = await index_document_to_pgvector(temp_file_path, document_id, thread_id, user_id)
        logger.info(f"File '{file.filename}' (document_id: {document_id}) successfully indexed to PGVector.")

        return {"document_id": document_id, "message": f"File {file.filename} uploaded and indexed successfully."}
    except Exception as e:
        logger.error(f"An unexpected error occurred during upload of '{file.filename}': {e}", exc_info=True)
        if document_id is not None:
            if chunk_ids:
                try:
                    await delete_document_from_pgvector(chunk_ids)
                    logger.info(f"Attempted cleanup of PGVector for document {document_id} after unexpected error.")
                except Exception as pgvector_clean_err:
                    logger.error(
                        f"Failed to cleanup PGVector for document {document_id} during error handling: {pgvector_clean_err}"
                    )
            await document_service.delete_document(document_id, session)
            logger.info(f"Rolled back database record for document {document_id} due to unexpected error.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while uploading '{file.filename}'.",
        )
    finally:
        if temp_file_path.exists():
            temp_file_path.unlink()


@document_router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(document_id: UUID, current_user: CurrentUserDep, session: SessionDep):
    """Delete a document from the database and PGVector."""
    chunk_message = ""
    document_chunks = await search_documents_in_pgvector(filter={"document_id": str(document_id)})
    if not document_chunks:
        logger.warning(f"Document chunks related to document {document_id} not found in PGVector.")
    else:
        doc_ids_to_delete = [doc.metadata["id"] for doc in document_chunks]
        await delete_document_from_pgvector(doc_ids_to_delete)
        logger.info(f"Successfully delete all document chunks related to document_id: {document_id} from PGVector.")
        chunk_message = "all its chunks from PGVector."
    await document_service.delete_document(document_id, session)
    logger.info(f"Successfully deleted document {document_id} from database.")
    message = f"Successfully deleted document {document_id} from database"

    return {"message": f"{message} and {chunk_message}."}
