import api_utils
import streamlit as st
from config import settings
from state_management import Page, change_thread, logout_user, new_chat, update_document_list, update_user_threads


def display_sidebar():
    st.sidebar.title("🔗Langgraph RAG Agent")
    if st.session_state["user"].is_authenticated:
        greeting_component()
        model_selection_component()
        chat_history_component()
        document_list_component()
        logout_component()
    else:
        authentication_component()


def authentication_component():
    st.sidebar.subheader("🔒 Authentication", divider="rainbow")
    col1, col2 = st.sidebar.columns(2)
    if col1.button("Login"):
        st.session_state["page"] = Page.LOGIN
    if col2.button("Register"):
        st.session_state["page"] = Page.REGISTER
    st.sidebar.markdown("**Please login or register for full acces.**")


def greeting_component():
    st.sidebar.subheader(f"👋 Welcome {st.session_state['user'].username}", divider="rainbow")
    if st.sidebar.button("New Chat"):
        new_chat()


def model_selection_component():
    st.sidebar.subheader("🤖 Select Model", divider="rainbow")
    st.session_state["model_name"] = st.sidebar.selectbox(
        "Select Model",
        options=settings.model_names,
        key="model",
        label_visibility="collapsed",
    )


def chat_history_component():
    st.sidebar.subheader("🗨️ Chat History", divider="rainbow")
    threads = st.session_state["user"].threads

    if threads:
        for thread in threads:
            col1, col2, col3 = st.sidebar.columns([0.15, 0.70, 0.15])
            with col1:
                if st.button("✅", key=f"select_{thread['id']}"):
                    change_thread(thread["id"])
            with col2:
                st.markdown(f"{thread['title']}")
            with col3:
                if st.button("❌", key=f"delete_{thread['id']}"):
                    with st.spinner(""):
                        delete_response = api_utils.delete_thread(thread["id"])
                        if delete_response.get("status") == "ok":
                            success_message = f"Thread with ID {thread['title']} deleted successfully."
                            st.sidebar.success(success_message)
                            update_user_threads()
                            new_chat()
                            st.rerun()
                        else:
                            st.sidebar.error("Failed to delete the thread")


def document_list_component():
    st.sidebar.subheader("📂 Document List", divider="rainbow")
    documents = st.session_state["thread"].documents
    if documents:
        for number, doc in enumerate(documents, start=1):
            col1, col2 = st.sidebar.columns([0.85, 0.15])
            with col1:
                st.markdown(f"{number}. {doc['file_name']}")
            with col2:
                if st.button("❌", key=f"delete_{doc['id']}"):
                    with st.spinner(""):
                        delete_response = api_utils.delete_document(doc["id"])
                        if delete_response:
                            success_message = f"Document with ID {doc['id']} deleted successfully."
                            st.sidebar.success(success_message)
                            update_document_list(st.session_state["thread"].id)
                            st.rerun()
                        else:
                            st.sidebar.error("Failed to delete the document")
    else:
        st.sidebar.write("No documents uploaded yet.")


def logout_component():
    st.sidebar.subheader("❌ Logout", divider="rainbow")
    if st.sidebar.button("logout"):
        logout_user()
        st.rerun()
