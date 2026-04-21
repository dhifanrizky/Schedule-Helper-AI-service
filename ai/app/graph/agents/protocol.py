from typing import Protocol
from app.graph.state import AppState


class Agent(Protocol):
    """
    Semua agent harus bisa dipanggil dengan state dan return dict.
    Tidak perlu inherit — cukup signature-nya cocok (duck typing).
    """
    def __call__(self, state: AppState) -> dict: ...