import logging
import traceback

from fastapi import HTTPException

from backend.repository.chat_repository import ChatRepository
from backend.repository.project_repository import ProjectRepository
from backend.schemas.chat import ChatMessage, ChatRequest, ChatResponse, ActionType
from backend.services.llm_provider import LLmProvider
from backend.services.project_service import ProjectService
import uuid
import re

logger = logging.getLogger(__name__)

from langchain_core.messages import HumanMessage
from backend.shared.builder import app as langgraph_app

class ChatService:
    def __init__(self, project_service: ProjectService,project_repository: ProjectRepository,llm_provider:LLmProvider, chat_repository: ChatRepository):
        self.project_service = project_service
        self.project_repository = project_repository
        self.llm_provider = llm_provider
        self.chat_repository = chat_repository


    async def chat(self, chat_request: ChatRequest):
        # 1. Guard check: If no project_id is in the request body, check if a project ID prefix 'pid_' is in the user's message.
        # If not, prompt them to provide their project ID.
        if not chat_request.project_id:
            import re
            # Matches variations like 'pid_123', 'pi d_4242', 'PID 123', 'p id_555' (case-insensitive)
            has_pid = bool(re.search(r'\b(p\s*i\s*d\s*[_\-\s]*[a-zA-Z0-9]+)', chat_request.message, re.IGNORECASE))
            if not has_pid:
                return ChatResponse(
                    message="Welcome! Got a Project ID (starts with 'pid_')? Enter it below to dive right in. No project yet? Let's build something awesome from scratch!",
                    name=chat_request.client_name,
                    action=ActionType.START_NEW_PROJECT
                )

        try:
            # Determine thread_id for LangGraph (either the project_id if present, or a new temporary thread_id)
            thread_id = chat_request.project_id or f"temp-{uuid.uuid4()}"

            # 2. Build initial state inputs for LangGraph
            inputs = {
                "messages": [HumanMessage(content=chat_request.message)],
                "project_id": chat_request.project_id,
            }

            # 3. Configure the run with a thread ID for session memory
            config = {"configurable": {"thread_id": thread_id}}

            # 4. Invoke the compiled LangGraph workflow
            final_state = await langgraph_app.ainvoke(inputs, config=config)

            # 5. Extract the final response text
            agent_text = final_state["messages"][-1].content if final_state.get("messages") else "I'm sorry, I encountered an issue."

            # 6. Extract the final verified/set project ID from state
            updated_project_id = final_state.get("project_id")

            # 7. Append to database/cache chat history for dashboard and historical reference
            chat_messages = [
                ChatMessage(role='user', text=chat_request.message),
                ChatMessage(role='model', text=agent_text),
            ]
            # if updated_project_id:
            #     await self.chat_repository.append_to_chat_history(project_id=updated_project_id, name_space='chat', chats=chat_messages)

            return ChatResponse(
                message=agent_text,
                name=chat_request.client_name,
                project_id=updated_project_id
            )

        except Exception as e:
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f'An error occurred while generating the LLM: {e}')
