import streamlit as st
from components import chat_history_component, document_list_component, model_selection_component


def display_sidebar():
    st.sidebar.title("🔗Langchain RAG Chatbot")
    chat_history_component()
    model_selection_component()
    document_list_component()
