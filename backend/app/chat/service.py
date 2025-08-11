import json
from collections.abc import AsyncGenerator, AsyncIterator
from uuid import UUID

from app.db.checkpointer import get_checkpointer
from fastapi import HTTPException
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from .langgraph_agent import build_retrival_graph, create_model
from .schemas import Message, PromptInput


async def simple_chat_stream(prompt_input: PromptInput) -> AsyncGenerator:
    model = create_model(model_name=prompt_input.model_name, streaming=True)
    async for chunk in model.astream([HumanMessage(content=prompt_input.prompt)]):
        if content := chunk.content:
            response = {"type": "llm_chunk", "content": str(content)}
            yield json.dumps(response) + "\n"


async def chat_stream(thread_id: UUID, prompt_input: PromptInput, user_id: UUID) -> AsyncIterator:
    """
    Streams the agent's execution steps and final response.
    """
    config = RunnableConfig(configurable={"thread_id": str(thread_id), "user_id": str(user_id)})
    checkpointer = await get_checkpointer()
    graph = build_retrival_graph(checkpointer, prompt_input.model_name)

    return graph.astream(
        input={"messages": [HumanMessage(content=prompt_input.prompt)], "retry_count": 0},
        config=config,
        stream_mode=["updates", "messages"],
    )


async def get_chat_history(thread_id: UUID, user_id: UUID) -> list[Message]:
    config = RunnableConfig(configurable={"thread_id": str(thread_id), "user_id": str(user_id)})
    checkpointer = await get_checkpointer()
    checkpoint = await checkpointer.aget(config)

    if checkpoint is None:
        raise HTTPException(status_code=404, detail="Chat history not found")

    all_messages = checkpoint.get("channel_values", {}).get("messages", [])
    messages = [
        Message(role=message.type, content=message.content)
        for message in all_messages
        if message.content and message.type in ["human", "ai"]
    ]

    return messages
