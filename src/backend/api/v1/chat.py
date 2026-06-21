from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models.account import Account
from backend.schemas.chat import ChatResponse, ChatRequest
from backend.api.dependencies import get_current_account, get_db, get_cosmos_db, get_llm_provider
from backend.services.llm_provider import LLmProvider

router = APIRouter(prefix='/chat', tags=['Chat'])


@router.post('/', response_model=ChatResponse)
async def chat(chat_request: ChatRequest,
         account: Account = Depends(get_current_account),
         db: Session = Depends(get_cosmos_db),
         llm:LLmProvider = Depends(get_llm_provider)
         ):
    # 1. check does the client exist in my db? if yes then check the clients old messages else make just create a client in the db
    # 2. find the message intent

    try:
        llm_response = await llm.generate_text(chat_request.message)
        print(llm_response)
        return ChatResponse(message=llm_response, name=chat_request.client_name)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'An error occurred while generating the LLM: {e}')

