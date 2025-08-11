import config  # need to import for config initialization # noqa: F401
import streamlit as st
from pages import home_page, login_page, register_page
from sidebar import display_sidebar
from state_management import Page, initialize_state

st.set_page_config(page_title="LangGraph RAG Agent", layout="wide", page_icon="🔗")


def main():
    initialize_state()
    display_sidebar()
    if st.session_state["page"] == Page.HOME:
        home_page()
    elif st.session_state["page"] == Page.LOGIN:
        login_page()
    elif st.session_state["page"] == Page.REGISTER:
        register_page()


if __name__ == "__main__":
    main()
