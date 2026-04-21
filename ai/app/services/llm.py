from functools import lru_cache
from langchain_openai import ChatOpenAI
from app.config import settings


@lru_cache
def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=settings.openai_api_key, # type: ignore
        model=settings.openai_model,
        temperature=0.7,
    )