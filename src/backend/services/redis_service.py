import json
from redis.asyncio import Redis

from backend.schemas.chat import ChatMessage


async def insert_chats(redis_client:Redis, redis_key, chat_messages: list[ChatMessage]):

    message_dic_list= [msg.model_dump() for msg in chat_messages]
    message_json_string = json.dumps(message_dic_list)
    async with redis_client.pipeline(transaction=True) as pipe:
        pipe.rpush(redis_key, message_json_string)
        pipe.ltrim(redis_key, -10, -1)
        pipe.expire(redis_key, 4800)

        await pipe.execute()


async def get_old_chats(redis_client:Redis, redis_key:str) -> list[ChatMessage]:
    raw_messages = await redis_client.lrange(redis_key, 0, -1)
    if not raw_messages:
        return []

    chat_history = []

    for msg_string in raw_messages:
        if msg_string.startswith("["):
            message_dicts = json.loads(msg_string)
            for msg_dict in message_dicts:
                chat_history.append(ChatMessage.model_validate(msg_dict))
        else:
            chat_history.append(ChatMessage.model_validate_json(msg_string))

    return chat_history