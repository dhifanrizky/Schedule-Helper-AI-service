from langgraph.checkpoint.redis import AsyncRedisSaver
from app.config import settings
from typing import Any

_checkpointer: AsyncRedisSaver | None = None
_checkpointer_cm: Any | None = None


async def init_checkpointer() -> AsyncRedisSaver:
    global _checkpointer, _checkpointer_cm
    if _checkpointer is None:
        _checkpointer_cm = AsyncRedisSaver.from_conn_string(settings.redis_url)
        _checkpointer = await _checkpointer_cm.__aenter__()
    return _checkpointer # type: ignore


async def get_checkpointer() -> AsyncRedisSaver:
    if _checkpointer is None:
        return await init_checkpointer()
    return _checkpointer


async def close_checkpointer() -> None:
    global _checkpointer, _checkpointer_cm
    if _checkpointer_cm is not None:
        await _checkpointer_cm.__aexit__(None, None, None)
        _checkpointer_cm = None
        _checkpointer = None