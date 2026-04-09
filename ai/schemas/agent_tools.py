from pydantic import BaseModel, Field
from typing import Union

class GetWeather(BaseModel):
    """Ambil data cuaca."""
    location: str

class FinalResponse(BaseModel):
    """Jawaban langsung ke user."""
    answer: str

# Router Schema
class AgentAction(BaseModel):
    action: Union[GetWeather, FinalResponse]
