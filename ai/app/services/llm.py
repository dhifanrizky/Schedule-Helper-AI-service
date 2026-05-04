from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from app.config import settings

def get_llm(provider: str, model: str, temperature: float = 0.0, **kwargs):
    """
    Factory function untuk mengembalikan model AI secara spesifik.
    """
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY tidak ditemukan di environment (.env atau secrets)")
        return ChatOpenAI(
            api_key=settings.openai_api_key, # type: ignore
            model=model,
            temperature=temperature
        )
        
    elif provider == "groq":
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY tidak ditemukan di environment (.env atau secrets)")
        return ChatGroq(
            api_key=settings.groq_api_key, # type: ignore
            model=model,
            temperature=temperature,
            model_kwargs=kwargs
        )
    
    elif provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY tidak ditemukan di environment (.env atau secrets)")
        return ChatGoogleGenerativeAI(
            api_key=settings.gemini_api_key, # type: ignore
            model=model,
            temperature=temperature,
            model_kwargs=kwargs
        )

    else:
        raise ValueError(f"Provider LLM '{provider}' belum didukung.")