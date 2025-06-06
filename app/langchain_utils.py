import logging

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from app.chroma_utils import vector_store
from app.config import settings
from app.schemas import ModelOptions

logger = logging.getLogger(__name__)

retriever = vector_store.as_retriever(search_kwargs={"k": 3})

contextualize_q_system_prompt = """
Given a chat history and the latest user question
which might reference context in the chat history,
formulate a standalone question which can be understood
without the chat history. Do NOT answer the question,
just reformulate it if needed and otherwise return it as is.
"""

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ]
)

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful AI assistant"),
        ("system", "Context: {context}"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ]
)


def get_retrieval_chain(model_name: str = ModelOptions.GPT_4O_MINI) -> Runnable:
    """Create a retrieval chain based on the provided model name."""

    if settings.api_key.get_secret_value().startswith("ghp_"):
        logger.info("Using GitHub Personal Access Token")
        llm = ChatOpenAI(
            model=f"openai/{model_name}",
            base_url="https://models.github.ai/inference",
            api_key=settings.api_key,
        )
    else:
        llm = ChatOpenAI(model=model_name, api_key=settings.api_key)
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    combine_docs_chain = create_stuff_documents_chain(llm, qa_prompt)

    return create_retrieval_chain(history_aware_retriever, combine_docs_chain)
