from fastapi import APIRouter, Depends, HTTPException
from backend.models.account import Account
from backend.schemas.chat import ChatResponse, ChatRequest, ChatMessage
from backend.api.dependencies import get_current_account, get_llm_provider, get_project_service,get_chat_service
from backend.services.chat_service import ChatService
from backend.services.llm_provider import LLmProvider
from backend.models.llm import IntentType
from backend.services.project_service import ProjectService

router = APIRouter(prefix='/chat', tags=['Chat'])

@router.post('/', response_model=ChatResponse)
async def chat(chat_request: ChatRequest,
         account: Account = Depends(get_current_account),
         llm:LLmProvider = Depends(get_llm_provider),
         project_service: ProjectService = Depends(get_project_service),
         chat_service: ChatService = Depends(get_chat_service),
         ):

    try:
        project_details= await project_service.get_project_details(project_id=chat_request.project_id)

        old_chats= await chat_service.get_old_chats(project_id=chat_request.project_id)

        llm_response = await llm.generate_text(prompt=chat_request.message,old_chats=old_chats or [],context_data=project_details.model_dump() if project_details else {})


        chat_messages = [
            ChatMessage(role='user', text=chat_request.message),
            ChatMessage(role='model', text=llm_response.text),
        ]

        await chat_service.append_to_chat_history(project_id=chat_request.project_id,name_space= 'chat', chats=chat_messages)


        return ChatResponse(message=llm_response.text, name=chat_request.client_name)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'An error occurred while generating the LLM: {e}')

