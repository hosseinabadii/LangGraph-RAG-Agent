import streamlit as st
from chat_interface import display_chat_interface
from sidebar import display_sidebar

if "session_id" not in st.session_state:
    st.session_state["session_id"] = None

if "session_history" not in st.session_state:
    st.session_state["session_history"] = []


if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "documents" not in st.session_state:
    st.session_state["documents"] = []

st.set_page_config(page_title="Langchain RAG Chatbot", layout="wide")

st.title("Hello, I'm Langchain RAG Chatbot!")
st.write("Please select a model and upload a document to get started.")

display_sidebar()
display_chat_interface()
