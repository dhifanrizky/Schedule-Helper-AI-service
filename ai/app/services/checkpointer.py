from langgraph.checkpoint.redis import RedisSaver
from app.config import settings
from typing import Any

_checkpointer: RedisSaver | None = None
_checkpointer_cm: Any | None = None


def init_checkpointer() -> RedisSaver:
    global _checkpointer, _checkpointer_cm
    if _checkpointer is None:
        _checkpointer_cm = RedisSaver.from_conn_string(settings.redis_url)
        _checkpointer = _checkpointer_cm.__enter__()
    assert _checkpointer is not None
    return _checkpointer

def get_checkpointer() -> RedisSaver:
    if _checkpointer is None:
        return init_checkpointer()
    assert _checkpointer is not None
    return _checkpointer


def close_checkpointer() -> None:
    global _checkpointer, _checkpointer_cm
    if _checkpointer_cm is not None:
        _checkpointer_cm.__exit__(None, None, None)
        _checkpointer_cm = None
        _checkpointer = None