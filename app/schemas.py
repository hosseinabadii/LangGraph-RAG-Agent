from enum import StrEnum

from pydantic import BaseModel, Field


class ModelOptions(StrEnum):
    OPENAI_GPT_4O_MINI = "openai/gpt-4o-mini"
    OPENAI_GPT_4O = "openai/gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"


class PromptInput(BaseModel):
    question: str
    model: ModelOptions = Field(default=ModelOptions.OPENAI_GPT_4O_MINI)


class PromptResponse(BaseModel):
    answer: str
    model: ModelOptions


class ResponseFormatter(BaseModel):
    """Always use this tool to structure your response to the user."""

    answer: str = Field(description="The answer to the user's question")
