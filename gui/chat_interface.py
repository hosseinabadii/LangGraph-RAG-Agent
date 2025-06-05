import streamlit as st
from api_utils import get_api_response


def display_chat_interface():
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
                st.session_state["session_id"] = response.get("session_id")
                st.session_state["messages"].append({"role": "assistant", "content": response["answer"]})

                with st.chat_message("assistant"):
                    st.markdown(response["answer"])

                    with st.expander("Response Details"):
                        st.subheader("Generated Answer")
                        st.code(response["answer"], language="markdown")
                        st.subheader("Model Name")
                        st.code(response["model"], language="markdown")
                        st.subheader("Session ID")
                        st.code(response["session_id"], language="markdown")
            else:
                st.error("An error occurred while processing your request. Please try again.")
