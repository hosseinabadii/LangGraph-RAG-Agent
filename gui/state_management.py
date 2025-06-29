from uuid import UUID

import streamlit as st
from api_utils import get_chat_history, list_document


def initialize_state():
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = None

    if "session_history" not in st.session_state:
        st.session_state["session_history"] = []

    if "session_title_mapping" not in st.session_state:
        st.session_state["session_title_mapping"] = {}

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    if "documents" not in st.session_state:
        st.session_state["documents"] = []


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
    st.rerun()


def update_chat_history(session_id: UUID) -> None:
    chat_history = get_chat_history(session_id)
    st.session_state["session_id"] = session_id
    st.session_state["messages"] = chat_history
    st.rerun()
