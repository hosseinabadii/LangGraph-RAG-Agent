from enum import StrEnum

import streamlit as st
from api_utils import delete_document, get_api_response, upload_document
from state_management import create_new_chat, update_chat_history, update_document_list_state


class ModelOptions(StrEnum):
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"


def model_selection_component():
    st.sidebar.subheader("🤖 Select Model", divider="rainbow")
    model_options = [ModelOptions.GPT_4O_MINI, ModelOptions.GPT_4O]
    st.sidebar.selectbox("Select Model", options=model_options, key="model", label_visibility="collapsed")


def upload_document_component():
    st.subheader("📂 Upload Document", divider="blue")
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "txt"], label_visibility="collapsed")
    if uploaded_file is not None:
        if st.button("Upload"):
            with st.spinner("Uploading..."):
                upload_response = upload_document(uploaded_file)
                if upload_response:
                    success_message = (
                        f"File {uploaded_file.name} uploaded successfully with ID {upload_response['file_id']}"
                    )
                    st.success(success_message)
                    update_document_list_state()
                    st.rerun()
                else:
                    st.error("Failed to upload file. Please try again.")


def document_list_component():
    st.sidebar.subheader("📂 Document List", divider="rainbow")
    if st.session_state["session_id"] is None:
        update_document_list_state()

    documents = st.session_state["documents"]
    if documents:
        for number, doc in enumerate(documents, start=1):
            col1, col2 = st.sidebar.columns([0.85, 0.15])
            with col1:
                st.markdown(f"{number}. {doc['file_name']}")
            with col2:
                if st.button("❌", key=f"delete_{doc['id']}"):
                    with st.spinner(""):
                        delete_response = delete_document(doc["id"])
                        if delete_response:
                            success_message = f"Document with ID {doc['id']} deleted successfully."
                            st.sidebar.success(success_message)
                            update_document_list_state()
                            st.rerun()
                        else:
                            st.sidebar.error("Failed to delete the document")
    else:
        st.sidebar.write("No documents uploaded yet.")


def chat_history_component():
    st.sidebar.subheader("🗨️ Chat History", divider="rainbow")

    if st.sidebar.button("New Chat"):
        create_new_chat()

    session_history = st.session_state["session_history"]
    if session_history:
        current_session_id_index = 0
        if st.session_state["session_id"] is not None:
            current_session_id_index = session_history.index(st.session_state["session_id"])
        selected_session_id = st.sidebar.radio(
            label="Select a chat",
            options=session_history,
            index=current_session_id_index,
            format_func=lambda x: st.session_state["session_title_mapping"].get(x, "No title chat"),
            key="selected_session",
            label_visibility="collapsed",
        )
        if (
            st.session_state["session_id"]
            and selected_session_id
            and st.session_state["session_id"] != selected_session_id
        ):
            update_chat_history(selected_session_id)


def chat_interface_component():
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about your documents"):
        st.session_state["messages"].append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Generating response..."):
            response = get_api_response(prompt, st.session_state["session_id"], st.session_state["model"])
            if response:
                answer = response.get("answer")
                with st.chat_message("assistant"):
                    st.markdown(answer)
                st.session_state["messages"].append({"role": "assistant", "content": answer})

                session_id = response.get("session_id")
                st.session_state["session_id"] = session_id

                if session_id not in st.session_state["session_history"]:
                    st.session_state["session_history"].append(session_id)
                    st.session_state["session_title_mapping"][session_id] = f"{prompt[:100]}..."
                    st.rerun()

            else:
                st.error("An error occurred while processing your request. Please try again.")
