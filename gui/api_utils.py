import logging
from uuid import UUID

import httpx
from config import settings
from streamlit.runtime.uploaded_file_manager import UploadedFile

BASE_URL = settings.base_url
TIMEOUT = settings.timeout

logger = logging.getLogger(__file__)


def get_api_response(question: str, session_id: str | None, model: str) -> dict | None:
    """
    Sends a question to the chat API and retrieves the response.

    Args:
        question: The question to send to the API.
        session_id: The session ID for the chat, if any.
        model: The model to be used by the API.

    Returns:
        A dictionary containing the API response JSON, or None if an error occurs.
    """
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    data = {"question": question, "model": model}

    if session_id:
        data["session_id"] = session_id

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.post(f"{BASE_URL}/chat", headers=headers, json=data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"API response failed with status {e.response.status_code}. Response: {e.response.text}")
        return None
    except httpx.RequestError as e:
        logger.error(f"API call failed with httpx.RequestError: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"API call failed with an unexpected exception: {str(e)}")
        return None


def get_chat_history(session_id: UUID) -> list:
    """
    Retrieves the chat history for a specific session ID.

    Args:
        session_id: The UUID of the chat session.

    Returns:
        A list of chat history messages.
    """

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(f"{BASE_URL}/chat/{session_id}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"API response failed with status {e.response.status_code}. Response: {e.response.text}")
        return []
    except httpx.RequestError as e:
        logger.error(f"API call failed with httpx.RequestError: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"API call failed with an unexpected exception: {str(e)}")
        return []


def upload_document(file: UploadedFile) -> dict | None:
    """
    Uploads a document to the API.

    Args:
        file: The UploadedFile object from Streamlit.

    Returns:
        A dictionary containing the API response JSON if successful, or None otherwise.
    """

    logger.info(f"Starting document upload for file: {file.name}")
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}

        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.post(f"{BASE_URL}//documents/uploadt", files=files)
            response.raise_for_status()

        logger.info(f"Successfully uploaded file: {file.name}")
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Upload failed with status {e.response.status_code}. Response: {e.response.text}")
        return None
    except httpx.RequestError as e:
        logger.error(f"File upload failed with httpx.RequestError: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"File upload failed with an unexpected exception: {str(e)}")
        return None


def list_document() -> list | None:
    """
    Retrieves the list of documents from the API.

    Returns:
        A list of documents if successful, or None otherwise.
    """

    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.get(f"{BASE_URL}/documents")
            response.raise_for_status()

        logger.info("Successfully retrieved document list")
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"List documents failed with status {e.response.status_code}. Response: {e.response.text}")
        return None
    except httpx.RequestError as e:
        logger.error(f"List documents failed with httpx.RequestError: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"List documents failed with an unexpected exception: {str(e)}")
        return None


def delete_document(file_id: str) -> bool:
    """
    Deletes a document from the API using its file ID.

    Args:
        file_id: The ID of the file to delete.

    Returns:
        True if deletion was successful, False otherwise.
    """

    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            response = client.delete(f"{BASE_URL}/documents/{file_id}", headers=headers)
            response.raise_for_status()

        logger.info(f"Successfully deleted document with ID: {file_id}")
        return True
    except httpx.HTTPStatusError as e:
        logger.error(f"Delete document failed with status {e.response.status_code}. Response: {e.response.text}")
        return False
    except httpx.RequestError as e:
        logger.error(f"Delete document failed with httpx.RequestError: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Delete document failed with an unexpected exception: {str(e)}")
        return False
