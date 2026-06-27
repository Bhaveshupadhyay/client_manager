from backend.schemas.chat import ChatMessage
from backend.services.redis_service import cached


@cached(
    namespace="chat",
    key=['project_id'],
    redis_ttl=4800,
    return_type=ChatMessage,
)
async def get_old_chats(project_id:str) -> list[ChatMessage]:
    #TODO: add a logic to fetch chats from cosmosDb
    return []