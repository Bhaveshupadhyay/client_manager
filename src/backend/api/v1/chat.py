from fastapi import APIRouter, Depends

from backend.models.account import Account
from backend.schemas.chat import ChatResponse
from backend.api.dependencies import get_current_account

router = APIRouter(prefix='/chat', tags=['Chat'])


@router.post('/', response_model=ChatResponse)
def chat(chat_request: ChatResponse, account: Account = Depends(get_current_account)):
    # Placeholder for chat logic
    return ChatResponse(message=chat_request.message, name=account.api_key.key_string)
