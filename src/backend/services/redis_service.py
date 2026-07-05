import inspect
import json
import logging
from functools import wraps
from typing import Optional, Type, Any
from backend.core.client import get_redis_client

from pydantic import TypeAdapter

logger = logging.getLogger(__name__)
def cached(
        namespace: str = "default",
        key: Optional[list[str]] = None,
        redis_ttl: int = 3600,
        return_type: Optional[Type[Any]] = None,
):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            func_args = bound_args.arguments

            if not key:
                return Exception('Key is required.')
            key_parts = [str(func_args.get(k)) for k in key]
            cache_key = get_redis_key(namespace=namespace,key_parts=key_parts)

            cached_data = await get_redis_client().get(cache_key)

            if cached_data:
                logger.info(f"[CACHE HIT] Returning data for {cache_key}")
                if return_type:
                    return TypeAdapter(return_type).validate_json(cached_data)
                return json.loads(cached_data)

            logger.info(f"[CACHE MISS] Executing function for {cache_key}")

            result = await func(*args, **kwargs)

            if result is not None:
                if return_type:
                    data_to_store = TypeAdapter(return_type).dump_json(result).decode('utf-8')
                else:
                    data_to_store = json.dumps(result)

                await get_redis_client().set(key=cache_key, ex=redis_ttl, value=data_to_store)
            return result
        return wrapper
    return decorator


async def insert_redis_data(
        key: str,
        namespace: str = "default",
        redis_ttl: int = 3600,
        data: Any = None,
):
    await get_redis_client().set(key=get_redis_key(namespace=namespace,key_parts=[key]), value=json.dumps(data), ex=redis_ttl)


def get_redis_key(namespace: str, key_parts: list[str]) -> str:
    return f"{namespace}:{':'.join(key_parts)}"
