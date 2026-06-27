import inspect
import json
from functools import wraps
from typing import Optional, Type, Any
from urllib.request import Request

from pydantic import BaseModel
from redis.asyncio import Redis

from backend.schemas.chat import ChatMessage

def cached(
        namespace: str = "default",
        key: Optional[list[str]] = None,
        redis_ttl: int = 3600,
        return_type: Optional[Type[Any]] = None,
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            func_args = bound_args.arguments

            request: Request = kwargs.get("request")
            if not request:
                raise ValueError("You must pass 'request: Request' to the cached function.")

            redis_client = request.app.state.redis


            if not key:
                return Exception('Key is required.')
            key_parts = [str(func_args.get(k)) for k in key]
            cache_key = f"{namespace}:{':'.join(key_parts)}"

            cached_data = redis_client.get(cache_key)

            if cached_data:
                print(f"[CACHE HIT] Returning data for {cache_key}")
                if return_type and issubclass(return_type, BaseModel):
                    return return_type.model_validate_json(cached_data)
                return json.loads(cached_data)

            print(f"[CACHE MISS] Executing function for {cache_key}")

            result = func(*args, **kwargs)

            if result is not None:
                if isinstance(result, BaseModel):
                    data_to_store = result.model_dump_json()
                else:
                    data_to_store = json.dumps(result)

                redis_client.setex(cache_key, redis_ttl, data_to_store)

            return result
        return wrapper
    return decorator

async def insert_chats(redis_client:Redis, redis_key, chat_messages: list[ChatMessage]):

    message_dic_list= [msg.model_dump() for msg in chat_messages]
    message_json_string = json.dumps(message_dic_list)
    async with redis_client.pipeline(transaction=True) as pipe:
        pipe.rpush(redis_key, message_json_string)
        pipe.ltrim(redis_key, -10, -1)
        pipe.expire(redis_key, 4800)

        await pipe.execute()


