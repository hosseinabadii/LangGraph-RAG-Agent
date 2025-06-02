from collections import defaultdict
from uuid import uuid4

from fastapi import FastAPI

from app.langchain_utils import get_chain
from app.schemas import PromptInput, PromptResponse, ResponseFormatter

app = FastAPI()

users_chat_history = defaultdict(list)


@app.post("/chat", response_model=PromptResponse)
async def chat(prompt_input: PromptInput):
    session_id = prompt_input.session_id
    if not session_id:
        session_id = uuid4()
    chat_history = users_chat_history[str(session_id)]
    chain = get_chain(prompt_input.model)
    response: ResponseFormatter = chain.invoke({"input": prompt_input.question, "chat_history": chat_history})
    answer = response.answer
    chat_history.extend(
        [
            {"role": "human", "content": prompt_input.question},
            {"role": "ai", "content": answer},
        ]
    )

    return PromptResponse(answer=response.answer, model=prompt_input.model, session_id=session_id)
