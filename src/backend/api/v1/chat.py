from fastapi import APIRouter, Depends
from backend.models.account import Account
from backend.schemas.chat import ChatResponse, ChatRequest
from backend.core.dependencies import get_current_account,get_chat_service
from backend.services.chat_service import ChatService

router = APIRouter(prefix='/chat', tags=['Chat'])

@router.post('/', response_model=ChatResponse)
async def chat(chat_request: ChatRequest,
         account: Account = Depends(get_current_account),
         chat_service: ChatService = Depends(get_chat_service),
         ):
    return await chat_service.chat(chat_request=chat_request,)

