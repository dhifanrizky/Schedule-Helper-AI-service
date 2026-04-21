from functools import lru_cache
from langgraph.checkpoint.redis import RedisSaver
from app.config import settings


@lru_cache
def get_checkpointer():
    """
    Redis checkpointer untuk persist state graph antar request.
    Wajib ada untuk HITL — tanpa ini graph tidak bisa pause dan resume.
    """
    with RedisSaver.from_conn_string(settings.redis_url) as saver:
        yield saver