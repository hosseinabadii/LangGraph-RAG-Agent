import logging
import shutil
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, UploadFile

from app.chroma_utils import DOCUMENT_LOADER_MAPPING, delete_document_from_chroma, index_document_to_chroma
from app.config import BASE_DIR
from app.database import (
    delete_document_record,
    get_chat_history,
    insert_chat_history,
    insert_document_record,
    list_document_record,
)
from app.langchain_utils import get_retrieval_chain
from app.schemas import (
    DocumentDeleteResponse,
    DocumentInfo,
    DocumentUploadResponse,
    Message,
    PromptInput,
    PromptResponse,
)

logger = logging.getLogger(__name__)
api_router = APIRouter()


@api_router.post("/chat", response_model=PromptResponse)
async def chat(prompt_input: PromptInput):
    session_id = prompt_input.session_id
    logger.info(f"Session ID: {str(session_id)}, User Prompt: {prompt_input.question}, Model: {prompt_input.model}")

    if not session_id:
        session_id = uuid4()

    chat_history = await get_chat_history(str(session_id))
    chain = get_retrieval_chain(prompt_input.model)
    response: dict = chain.invoke({"input": prompt_input.question, "chat_history": chat_history})
    answer = response.get("answer", "No answer found")
    metadata = [item.metadata for item in response.get("context", [])]

    await insert_chat_history(str(session_id), prompt_input.question, answer, prompt_input.model)
    logger.info(f"Session ID: {str(session_id)}, AI Response: {str(answer)[:100]}...")

    return {"answer": answer, "metadata": metadata, "model": prompt_input.model, "session_id": session_id}


@api_router.get("/chat/{session_id}", response_model=list[Message])
async def fetch_chat_history(session_id: UUID):
    return await get_chat_history(str(session_id))


@api_router.get("/documents", response_model=list[DocumentInfo])
async def list_documents():
    return await list_document_record()


@api_router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile):
    if file.filename is None:
        logger.error("No file uploaded.")
        raise HTTPException(status_code=400, detail="No file uploaded.")

    allowd_extensions = list(DOCUMENT_LOADER_MAPPING.keys())
    message = f"Unsupported file type. Allowed types: {', '.join(allowd_extensions)}"
    if Path(file.filename).suffix not in allowd_extensions:
        logger.error(message)
        raise HTTPException(status_code=400, detail=message)

    TEMP_DIR = BASE_DIR / "tmp"
    if not TEMP_DIR.exists():
        TEMP_DIR.mkdir()
    temp_file_path = TEMP_DIR / file.filename
    file_id = None

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"File '{file.filename}' saved temporarily to '{temp_file_path}'.")

        file_id = await insert_document_record(file.filename)
        if file_id is None:
            logger.error(f"Failed to insert document record for '{file.filename}' into database.")
            raise HTTPException(status_code=500, detail="Failed to create document record in database.")
        logger.info(f"Document record inserted for '{file.filename}' with file_id: {file_id}.")

        index_document_to_chroma(temp_file_path, file_id)
        logger.info(f"File '{file.filename}' (file_id: {file_id}) successfully indexed to Chroma.")

        return {"message": f"File {file.filename} uploaded and indexed successfully.", "file_id": file_id}
    except Exception as e:
        logger.error(f"An unexpected error occurred during upload of '{file.filename}': {e}", exc_info=True)
        if file_id is not None:
            try:
                delete_document_from_chroma(file_id)
                logger.info(f"Attempted cleanup of Chroma for file_id: {file_id} after unexpected error.")
            except Exception as chroma_clean_err:
                logger.error(
                    f"Failed to cleanup Chroma for file_id: {file_id} during error handling: {chroma_clean_err}"
                )
            await delete_document_record(file_id)
            logger.info(f"Rolled back database record for file_id: {file_id} due to unexpected error.")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while uploading '{file.filename}'.")
    finally:
        if temp_file_path.exists():
            temp_file_path.unlink()


@api_router.delete("/documents/{file_id}", response_model=DocumentDeleteResponse)
async def delete_document(file_id: int):
    logger.info(f"Attempting to delete document with file_id: {file_id}.")
    try:
        delete_document_from_chroma(file_id)
        logger.info(f"Successfully deleted document chunks for file_id: {file_id} from Chroma.")
    except Exception as e:
        logger.error(f"Unexpected error deleting document {file_id} from Chroma: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while deleting document {file_id} from vector store.",
        )

    db_delete_success = await delete_document_record(file_id)
    if not db_delete_success:
        logger.warning(
            f"Document with file_id: {file_id} not found in database or failed to delete (already deleted from Chroma)."
        )
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID {file_id} not found or could not be deleted.",
        )

    return {"message": f"Document with ID {file_id} deleted successfully from chroma and database."}
