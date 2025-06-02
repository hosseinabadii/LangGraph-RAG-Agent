from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from app.config import settings
from app.schemas import ModelOptions, ResponseFormatter

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful AI assistant"),
        ("human", "{input}"),
    ]
)


def get_chain(model_name: str = ModelOptions.OPENAI_GPT_4O_MINI) -> Runnable:
    llm = ChatOpenAI(model=model_name, base_url=settings.base_url, api_key=settings.api_key)
    chain = qa_prompt | llm.with_structured_output(ResponseFormatter)

    return chain
