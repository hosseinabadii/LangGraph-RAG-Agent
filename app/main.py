import logging
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI

from app.database import get_chat_history, init_db, insert_chat_history
from app.langchain_utils import get_chain
from app.schemas import PromptInput, PromptResponse, ResponseFormatter

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    lifespan=lifespan,
)


@app.post("/chat", response_model=PromptResponse)
async def chat(prompt_input: PromptInput):
    session_id = prompt_input.session_id
    logger.info(f"Session ID: {str(session_id)}, User Prompt: {prompt_input.question}, Model: {prompt_input.model}")

    if not session_id:
        session_id = uuid4()

    chat_history = await get_chat_history(str(session_id))
    chain = get_chain(prompt_input.model)
    response: ResponseFormatter = chain.invoke({"input": prompt_input.question, "chat_history": chat_history})
    answer = response.answer

    await insert_chat_history(str(session_id), prompt_input.question, answer, prompt_input.model)
    logger.info(f"Session ID: {str(session_id)}, AI Response: {answer[:100]}...")

    return PromptResponse(answer=response.answer, model=prompt_input.model, session_id=session_id)
