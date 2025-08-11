from uuid import UUID

import httpx
import requests
import streamlit as st
from config import settings
from loguru import logger
from streamlit.runtime.uploaded_file_manager import UploadedFile

BASE_URL = settings.backend_base_url
TIMEOUT = 30

## Auth --------------------------------------------------------------------


def register_user(register_data: dict) -> dict:
    """
    Registers a user with the API.

    Args:
        register_data: A dictionary containing user registration data.

    Returns:
        A dictionary containing the API response JSON if successful, or an empty dictionary otherwise.
    """
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/signup", headers=headers, json=register_data, timeout=TIMEOUT)
        response.raise_for_status()

        logger.info("Successfully registered user")
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"Register user failed with status {e.response.status_code}. Response: {e.response.text}")
        if e.response.status_code in [401, 403]:
            return e.response.json()
        return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"Register user failed with RequestError: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"Register user failed with an unexpected exception: {str(e)}")
        return {}


def login_user(email: str, password: str) -> dict:
    """
    Logs in a user with the API.

    Args:
        email: The email of the user.
        password: The password of the user.

    Returns:
        A dictionary containing the API response JSON if successful, or an empty dictionary otherwise.
    """
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"username": email, "password": password}

    try:
        response = requests.post(f"{BASE_URL}/auth/login", headers=headers, data=data, timeout=TIMEOUT)
        response.raise_for_status()

        logger.info("Successfully logged in user")
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"Login user failed with status {e.response.status_code}. Response: {e.response.text}")
        if e.response.status_code in [401, 403]:
            return e.response.json()
        return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"Login user failed with RequestError: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"Login user failed with an unexpected exception: {str(e)}")
        return {}


## Chat --------------------------------------------------------------------


async def simple_chat_stream(chat_data: dict):
    """
    Calls the streaming chat endpoint and yields text chunks.

    Args:
        chat_data: Dictionary containing chat parameters

    Yields:
        str: Text chunks from the stream
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            async with client.stream("POST", f"{BASE_URL}/chat/", json=chat_data) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        yield line
        except httpx.HTTPStatusError as e:
            raise Exception(
                f"Chat server responded with error: {e.response.status_code} {e.response.reason_phrase}"
            ) from e
        except httpx.RequestError as e:
            raise Exception(f"Failed to connect to chat server: {str(e)}") from e


async def chat_stream(chat_data: dict, thread_id: UUID):
    """
    Calls the streaming chat endpoint and yields text chunks.
    This function is used for authenticated users, so it has a memory and access to the tools.

    Args:
        chat_data: Dictionary containing chat parameters

    Yields:
        str: Text chunks from the stream
    """
    headers = {
        "Authorization": f"Bearer {st.session_state['user'].access_token}",
    }
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=headers) as client:
        try:
            async with client.stream("POST", f"{BASE_URL}/chat/{thread_id}", json=chat_data) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        yield line
        except httpx.HTTPStatusError as e:
            raise Exception(
                f"Chat server responded with error: {e.response.status_code} {e.response.reason_phrase}"
            ) from e
        except httpx.RequestError as e:
            raise Exception(f"Failed to connect to chat server: {str(e)}") from e


def get_chat_history(thread_id: UUID) -> list | dict:
    """
    Retrieves the chat history for a specific s ID.

    Args:
        thread_id: The UUID of the chat session.

    Returns:
        A list of chat history messages.
    """
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {st.session_state['user'].access_token}",
    }

    try:
        response = requests.get(f"{BASE_URL}/chat/{thread_id}", headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"API response failed with status {e.response.status_code}. Response: {e.response.text}")
        if e.response.status_code in [401, 404]:
            return e.response.json()
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"API call failed with RequestError: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"API call failed with an unexpected exception: {str(e)}")
        return []


## Threads -----------------------------------------------------------------


def create_new_thread() -> dict:
    """
    Creates a new thread in the API.

    Returns:
        A dictionary containing the API response JSON.
    """

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {st.session_state['user'].access_token}",
    }

    try:
        response = requests.post(f"{BASE_URL}/threads/", headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(
            f"API call for 'create_new_thread' failed with status {e.response.status_code}. "
            "Response: {e.response.text}"
        )
        if e.response.status_code in [401]:
            return e.response.json()
        return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"API call for 'create_new_thread' failed with RequestError: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"API call for 'create_new_thread' failed with an unexpected exception: {str(e)}")
        return {}


def get_thread(thread_id: UUID) -> dict:
    """
    Retrieves a specific thread from the API.

    Args:
        thread_id: The UUID of the thread to retrieve.

    Returns:
        A dictionary containing the API response JSON.
    """

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {st.session_state['user'].access_token}",
    }

    try:
        response = requests.get(f"{BASE_URL}/threads/{thread_id}", headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(
            f"API call for 'get_thread' failed with status {e.response.status_code}. Response: {{{{e.response.text}}}}"
        )
        if e.response.status_code in [401, 403, 404]:
            return e.response.json()
        return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"API call for 'get_thread' failed with RequestError: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"API call for 'get_thread' failed with an unexpected exception: {str(e)}")
        return {}


def get_user_threads() -> list:
    """
    Retrieves the user's threads from the API.

    Returns:
        A dictionary containing the API response JSON.
    """

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {st.session_state['user'].access_token}",
    }
    try:
        response = requests.get(f"{BASE_URL}/threads/", headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(
            f"API call for 'get_user_threads' failed with status {e.response.status_code}. Response: {e.response.text}"
        )
        if e.response.status_code in [401]:
            return e.response.json()
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"API call for 'get_user_threads' failed with RequestError: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"API call for 'get_user_threads' failed with an unexpected exception: {str(e)}")
        return []


def update_thread(thread_id: UUID, title: str) -> dict:
    """
    Update an existing thread in the API.

    Args:
        thread_id: The UUID of the thread to update.
        title: The title of the thread to update.

    Returns:
        A dictionary containing the API response JSON.
    """

    headers = {
        # "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {st.session_state['user'].access_token}",
    }

    data = {"title": title}
    try:
        response = requests.patch(f"{BASE_URL}/threads/{thread_id}", json=data, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(
            f"API call for 'update_thread' failed with status {e.response.status_code}. Response: {e.response.text}"
        )
        if e.response.status_code in [401, 403, 404]:
            return e.response.json()
        return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"API call for 'update_thread' failed with RequestError: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"API call for 'update_thread' failed with an unexpected exception: {str(e)}")
        return {}


def delete_thread(thread_id: UUID) -> dict:
    """
    Deletes a thread from the API.

    Args:
        thread_id: The UUID of the thread to delete.

    Returns:
        A dictionary containing the response from the API.
    """

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {st.session_state['user'].access_token}",
    }

    try:
        response = requests.delete(f"{BASE_URL}/threads/{thread_id}", headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        return {"status": "ok", "detail": f"Thread with ID {thread_id} successfylly deleted."}
    except requests.exceptions.HTTPError as e:
        logger.error(
            f"API call for 'delete_thread' failed with status {e.response.status_code}. Response: {e.response.text}"
        )
        if e.response.status_code in [401, 403, 404]:
            return e.response.json()
        return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"API call for 'delete_thread' failed with RequestError: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"API call for 'delete_thread' failed with an unexpected exception: {str(e)}")
        return {}


## Documents ----------------------------------------------------------


def upload_document(thread_id: UUID, file: UploadedFile) -> dict | None:
    """
    Uploads a document to the API.

    Args:
        file: The UploadedFile object from Streamlit.

    Returns:
        A dictionary containing the API response JSON if successful, or None otherwise.
    """

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {st.session_state['user'].access_token}",
    }

    logger.info(f"Starting document upload for file: {file.name}")
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}

        response = requests.post(
            f"{BASE_URL}/documents/upload/{thread_id}", files=files, headers=headers, timeout=TIMEOUT
        )
        response.raise_for_status()

        logger.info(f"Successfully uploaded file: {file.name}")
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"Upload failed with status {e.response.status_code}. Response: {e.response.text}")
        if e.response.status_code in [400, 401]:
            return e.response.json()
        return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"File upload failed with RequestError: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"File upload failed with an unexpected exception: {str(e)}")
        return None


def list_document(thread_id: UUID) -> list | None:
    """
    Retrieves the list of documents from the API.

    Returns:
        A list of documents if successful, or None otherwise.
    """

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {st.session_state['user'].access_token}",
    }

    try:
        response = requests.get(f"{BASE_URL}/documents/{thread_id}", headers=headers, timeout=TIMEOUT)
        response.raise_for_status()

        logger.info("Successfully retrieved document list")
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"List documents failed with status {e.response.status_code}. Response: {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"List documents failed with RequestError: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"List documents failed with an unexpected exception: {str(e)}")
        return None


def delete_document(document_id: str) -> bool:
    """
    Deletes a document from the API using its file ID.

    Args:
        document_id: The ID of the file to delete.

    Returns:
        True if deletion was successful, False otherwise.
    """

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {st.session_state['user'].access_token}",
    }

    try:
        response = requests.delete(f"{BASE_URL}/documents/{document_id}", headers=headers, timeout=TIMEOUT)
        response.raise_for_status()

        logger.info(f"Successfully deleted document with ID: {document_id}")
        return True
    except requests.exceptions.HTTPError as e:
        logger.error(f"Delete document failed with status {e.response.status_code}. Response: {e.response.text}")
        if e.response.status_code in [401, 403, 404]:
            return e.response.json()
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Delete document failed with RequestError: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Delete document failed with an unexpected exception: {str(e)}")
        return False
