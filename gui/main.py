import streamlit as st
from chat_interface import display_chat_interface
from sidebar import display_sidebar

st.title("🔗Langchain RAG Chatbot")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "session_id" not in st.session_state:
    st.session_state["session_id"] = None

display_sidebar()
display_chat_interface()
