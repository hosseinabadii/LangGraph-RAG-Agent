import streamlit as st
from chat_interface import display_chat_interface
from sidebar import display_sidebar
from state_management import initialize_state

st.set_page_config(page_title="Langchain RAG Chatbot", layout="wide")


def main():
    initialize_state()
    display_sidebar()
    display_chat_interface()


if __name__ == "__main__":
    main()
