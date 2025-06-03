import logging
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile

from app.config import BASE_DIR
from app.database import (
    delete_document_record,
    get_chat_history,
    insert_chat_history,
    insert_document_record,
    list_document_record,
)
from app.langchain_utils import get_chain
from app.schemas import (
    DocumentDeleteResponse,
    DocumentInfo,
    DocumentUploadResponse,
    PromptInput,
    PromptResponse,
    ResponseFormatter,
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
    chain = get_chain(prompt_input.model)
    response: ResponseFormatter = chain.invoke({"input": prompt_input.question, "chat_history": chat_history})
    answer = response.answer

    await insert_chat_history(str(session_id), prompt_input.question, answer, prompt_input.model)
    logger.info(f"Session ID: {str(session_id)}, AI Response: {answer[:100]}...")

    return PromptResponse(answer=response.answer, model=prompt_input.model, session_id=session_id)


@api_router.get("/documents", response_model=list[DocumentInfo])
async def list_document():
    return await list_document_record()


@api_router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile):
    allowd_extensions = [".pdf", ".docx", ".txt"]

    if file.filename is None:
        logger.error("No file uploaded.")
        raise HTTPException(status_code=400, detail="No file uploaded.")

    if Path(file.filename).suffix not in allowd_extensions:
        logger.error(f"Unsupported file type. Allowed types: {', '.join(allowd_extensions)}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed types: {', '.join(allowd_extensions)}",
        )

    TEMP_DIR = BASE_DIR / "tmp"
    if not TEMP_DIR.exists():
        TEMP_DIR.mkdir()
    temp_file_path = TEMP_DIR / file.filename

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_id = await insert_document_record(file.filename)
        if file_id is None:
            logger.error("Failed to insert document record into database.")
            raise HTTPException(status_code=500, detail="Failed to insert document record into database.")

        return {"message": f"File {file.filename} uploaded successfully.", "file_id": file_id}
    except Exception as e:
        logger.error(f"Failed to save file to disk: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save file to disk")
    finally:
        if temp_file_path.exists():
            temp_file_path.unlink()


@api_router.delete("/documents/{file_id}", response_model=DocumentDeleteResponse)
async def delete_document(file_id: int):
    db_delete_success = await delete_document_record(file_id)
    if not db_delete_success:
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID {file_id} not found or could not be deleted.",
        )
    return {"message": f"Document with ID {file_id} deleted successfully from database."}
