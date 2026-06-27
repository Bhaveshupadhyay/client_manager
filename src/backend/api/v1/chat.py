from azure.cosmos import ContainerProxy
from fastapi import APIRouter, Depends, HTTPException
from pydantic import json
from redis.asyncio import Redis
from sqlalchemy.orm import Session

from backend.models.account import Account
from backend.schemas.chat import ChatResponse, ChatRequest, ChatMessage
from backend.api.dependencies import get_current_account, get_db, get_cosmos_db, get_llm_provider, \
    get_client_project_container, get_redis
from backend.services.database_service import get_project_details
from backend.services.llm_provider import LLmProvider
from backend.models.llm import IntentType
# from backend.services.redis_service import get_old_chats, insert_chats

router = APIRouter(prefix='/chat', tags=['Chat'])

@router.post('/', response_model=ChatResponse)
async def chat(chat_request: ChatRequest,
         account: Account = Depends(get_current_account),
         llm:LLmProvider = Depends(get_llm_provider),
         db_container: ContainerProxy = Depends(get_client_project_container),
         redis: Redis = Depends(get_redis)
         ):

    try:
        project_details= await get_project_details(project_id='fi_us_2026_4528',db_container=db_container)
        redis_key = f"chat:session:{project_details.project_id}"
        await redis.delete(redis_key)

        # old_chats= await get_old_chats(redis_client=redis, redis_key=redis_key)
        #
        # llm_response = await llm.generate_text(prompt=chat_request.message,old_chats=old_chats)
        #
        # chat_messages = [
        #     ChatMessage(role='user', text=chat_request.message),
        #     ChatMessage(role='model', text=llm_response.text),
        # ]
        #
        # await insert_chats(redis_client=redis, redis_key=redis_key,chat_messages=chat_messages,)

        return ChatResponse(message='llm_response.text', name=chat_request.client_name)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'An error occurred while generating the LLM: {e}')

