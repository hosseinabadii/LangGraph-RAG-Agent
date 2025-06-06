from enum import StrEnum
from uuid import UUID

import streamlit as st
from api_utils import delete_document, get_chat_history, list_document, upload_document


class ModelOptions(StrEnum):
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"


def update_document_list_state():
    documents = list_document()
    if documents is None:
        st.sidebar.error("Failed to retrieve document list. Please try again.")
        st.session_state["documents"] = []
    else:
        st.session_state["documents"] = documents


def create_new_chat():
    st.session_state["session_id"] = None
    st.session_state["messages"] = []
    st.session_state["documents"] = []
    st.rerun()


def update_chat_history(session_id: UUID) -> None:
    chat_history = get_chat_history(session_id)
    st.session_state["session_id"] = session_id
    st.session_state["messages"] = chat_history


def display_sidebar():
    st.sidebar.title("🔗Langchain RAG Chatbot")

    if st.sidebar.button("New Chat"):
        create_new_chat()

    session_history = st.session_state["session_history"]
    if session_history:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            current_session_id_index = 0
            if st.session_state["session_id"] is not None:
                current_session_id_index = session_history.index(st.session_state["session_id"])
            selected_session_id = st.selectbox(
                label="Select a chat",
                options=session_history,
                index=current_session_id_index,
                key="selected_session",
                label_visibility="collapsed",
            )
        with col2:
            if st.button("Select Chat"):
                update_chat_history(selected_session_id)

    # Sidebar: Model Selection
    st.sidebar.header("Select Model")
    model_options = [ModelOptions.GPT_4O_MINI, ModelOptions.GPT_4O]
    st.sidebar.selectbox("Select Model", options=model_options, key="model", label_visibility="collapsed")

    # Sidebar: Upload Document
    st.sidebar.header("Upload Document")
    uploaded_file = st.sidebar.file_uploader("Choose a file", type=["pdf", "docx", "txt"], label_visibility="collapsed")
    if uploaded_file is not None:
        if st.sidebar.button("Upload"):
            with st.spinner("Uploading..."):
                upload_response = upload_document(uploaded_file)
                if upload_response:
                    success_message = (
                        f"File {uploaded_file.name} uploaded successfully with ID {upload_response['file_id']}"
                    )
                    st.sidebar.success(success_message)
                    update_document_list_state()
                else:
                    st.sidebar.error("Failed to upload file. Please try again.")

    # Sidebar: List Documents
    st.sidebar.header("Uploaded Documents")
    if st.sidebar.button("Refresh Document List"):
        with st.spinner("Refreshing..."):
            update_document_list_state()

    if "documents" not in st.session_state:
        update_document_list_state()

    documents = st.session_state["documents"]
    if documents:
        for number, doc in enumerate(documents, start=1):
            st.sidebar.write(f"{number}. {doc['file_name']}")

        # DELETE DOCUMENT
        selected_file_id: str = st.sidebar.selectbox(
            "Select a document to delete",
            options=[doc["id"] for doc in documents],
            format_func=lambda file_id: next(doc for doc in documents if doc["id"] == file_id)["file_name"],
        )
        if st.sidebar.button("Delete Selected Document"):
            with st.spinner("Deleting..."):
                delete_response = delete_document(selected_file_id)
                if delete_response:
                    success_message = f"Document with ID {selected_file_id} deleted successfully."
                    st.sidebar.success(success_message)
                    update_document_list_state()
                else:
                    st.sidebar.error("Failed to delete the document")
    else:
        st.sidebar.write("No documents uploaded yet.")
