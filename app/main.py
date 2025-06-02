from fastapi import FastAPI

from app.langchain_utils import get_chain
from app.schemas import PromptInput, PromptResponse, ResponseFormatter

app = FastAPI()


@app.post("/chat", response_model=PromptResponse)
async def chat(prompt_input: PromptInput):
    chain = get_chain(prompt_input.model)
    response: ResponseFormatter = chain.invoke({"input": prompt_input.question})

    return PromptResponse(answer=response.answer, model=prompt_input.model)
