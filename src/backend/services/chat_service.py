from redis.asyncio import RedisCluster

from backend.schemas.chat import ChatMessage
from backend.services.redis_service import get_redis_key


class ChatService:
    def __init__(self, redis_client: RedisCluster):
        self.redis_client = redis_client

    async def get_old_chats(self,project_id:str) -> list[ChatMessage]:
        cache_key = get_redis_key(namespace="chat", key_parts=[project_id])

        raw_messages = await self.redis_client.lrange(cache_key, 0, -1)

        if raw_messages:
            return [ChatMessage.model_validate_json(msg) for msg in raw_messages]

        # TODO: Add logic to fetch chats from Cosmos DB
        cosmos_chats: list[ChatMessage] = []

        if cosmos_chats:
            message_json = [chat.model_dump_json() for chat in cosmos_chats]
            await self.redis_client.rpush(cache_key, *message_json)
            await self.redis_client.expire(cache_key, 4800)

        return cosmos_chats


    async def append_to_chat_history(self, project_id:str, name_space: str, chats: list[ChatMessage]):
        """Adds a single new message to the end of the Redis list."""
        cache_key = get_redis_key(namespace=name_space,key_parts=[project_id])

        if not chats:
            return

        message_json = [chat.model_dump_json() for chat in chats]

        await self.redis_client.rpush(cache_key, *message_json)

        await self.redis_client.ltrim(cache_key, -10, -1)

        await self.redis_client.expire(cache_key, 4800)


