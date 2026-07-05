from upstash_redis.asyncio import Redis

from backend.schemas.chat import ChatMessage
from backend.services.redis_service import get_redis_key
from backend.repository.chat_repository import ChatRepository
from backend.schemas.chat import ChatMessage, ChatRequest, ChatResponse
from backend.services.llm_provider import LLmProvider
from backend.services.project_service import ProjectService


class ChatService:
    def __init__(self, project_service: ProjectService,llm_provider:LLmProvider, chat_repository: ChatRepository):
        self.project_service = project_service
        self.llm_provider = llm_provider
        self.chat_repository = chat_repository


    async def get_old_chats(self,project_id:str) -> list[ChatMessage]:
        cache_key = get_redis_key(namespace="chat", key_parts=[project_id])

        raw_messages = await self.redis_client.lrange(cache_key, 0, -1)

        if raw_messages:
            return [ChatMessage.model_validate_json(msg) for msg in raw_messages]

        # TODO: Add logic to fetch chats from Cosmos DB
        cosmos_chats: list[ChatMessage] = []

    async def chat(self,chat_request: ChatRequest):
        project_details= await self.project_service.get_project_details(project_id=chat_request.project_id)

        old_chats= await self.chat_repository.get_old_chats(project_id=chat_request.project_id)

        llm_response = await self.llm_provider.generate_text(prompt=chat_request.message,old_chats=old_chats or [],context_data=project_details.model_dump() if project_details else {})


        chat_messages = [
            ChatMessage(role='user', text=chat_request.message),
            ChatMessage(role='model', text=llm_response.text),
        ]

        await self.chat_repository.append_to_chat_history(project_id=chat_request.project_id,name_space= 'chat', chats=chat_messages)

        return ChatResponse(message=llm_response.text, name=chat_request.client_name)


