import asyncio
import datetime
import logging
import re
import traceback
import uuid

from fastapi import HTTPException
from langchain_core.messages import HumanMessage

from backend.models.client import ProjectItem, ExtractedFacts
from backend.repository.chat_repository import ChatRepository
from backend.repository.project_repository import ProjectRepository
from backend.schemas.chat import ChatMessage, ChatRequest, ChatResponse, ServerActionType, ClientActionType
from backend.services.llm_provider import LLmProvider
from backend.services.project_service import ProjectService
from backend.shared.builder import app as langgraph_app

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, project_service: ProjectService, project_repository: ProjectRepository, llm_provider: LLmProvider, chat_repository: ChatRepository):
        self.project_service = project_service
        self.project_repository = project_repository
        self.llm_provider = llm_provider
        self.chat_repository = chat_repository

    async def chat(self, chat_request: ChatRequest) -> ChatResponse:
        active_project_id: str | None = None

        if chat_request.action_type == ClientActionType.START_NEW_PROJECT:
            new_project_id = self._generate_project_id()
            new_client_id = self._generate_client_id()
            await self.project_repository.create_project(ProjectItem(
                id=new_project_id,
                project_id=new_project_id,
                client_id=new_client_id,
                extracted_facts=ExtractedFacts(client_budget=0.0, estimated_cost=0.0, currency="USD", tech_stack=[], agreed_requirements=[])
            ))
            active_project_id = new_project_id

        elif chat_request.project_id:
            if not chat_request.project_id.startswith("pid_"):
                return ChatResponse(
                    message=f"Invalid project ID '{chat_request.project_id}'. You can find the project ID in the invoice we sent you from clientmanager.tech, or if you'd like we can start a new project!",
                    name=chat_request.client_name,
                    action=ServerActionType.START_NEW_PROJECT
                )

            project_details = await self.project_repository.get_project_details(chat_request.project_id)
            if not project_details:
                return ChatResponse(
                    message=f"We couldn't find project ID '{chat_request.project_id}' in our database. You can find the project ID in the invoice we sent you from clientmanager.tech, or if you'd like we can start a new project!",
                    name=chat_request.client_name,
                    action=ServerActionType.START_NEW_PROJECT
                )
            active_project_id = chat_request.project_id

        else:
            has_pid = bool(re.search(r'\b(p\s*i\s*d\s*[_\-\s]*[a-zA-Z0-9]+)', chat_request.message, re.IGNORECASE))
            if not has_pid:
                return ChatResponse(
                    message="Welcome! Got a Project ID (starts with 'pid_')? Enter it below to dive right in. No project yet? Let's build something awesome from scratch!",
                    name=chat_request.client_name,
                    action=ServerActionType.START_NEW_PROJECT
                )

        try:
            thread_id = active_project_id or f"temp-{uuid.uuid4()}"

            inputs = {
                "messages": [HumanMessage(content=chat_request.message)],
                "project_id": active_project_id,
            }

            config = {"configurable": {"thread_id": thread_id}}

            final_state = await asyncio.wait_for(
                langgraph_app.ainvoke(inputs, config=config),
                timeout=60.0
            )

            agent_text = final_state["messages"][-1].content if final_state.get("messages") else "I'm sorry, I encountered an issue."

            updated_project_id = final_state.get("project_id") or active_project_id
            updated_action = final_state.get("action")

            chat_messages = [
                ChatMessage(role='user', text=chat_request.message),
                ChatMessage(role='model', text=agent_text),
            ]
            if updated_project_id:
                try:
                    await self.chat_repository.append_to_chat_history(
                        project_id=updated_project_id,
                        name_space='chat',
                        chats=chat_messages
                    )
                except Exception as history_err:
                    logger.warning(f"Failed to persist chat history for project {updated_project_id}: {history_err}")

            return ChatResponse(
                message=agent_text,
                name=chat_request.client_name,
                project_id=updated_project_id,
                action=updated_action
            )

        except asyncio.TimeoutError:
            logger.error("LangGraph invocation timed out.")
            raise HTTPException(status_code=504, detail="Request processing timed out. Please try again.")

        except Exception as e:
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f'An error occurred while processing your message: {e}')

    def _generate_project_id(self) -> str:
        source = "fi"
        location = "us"
        current_year = datetime.datetime.now(datetime.timezone.utc).year
        short_uuid = uuid.uuid4().hex[:12]
        return f"pid_{source}_{location}_{current_year}_{short_uuid}"

    def _generate_client_id(self) -> str:
        source = "fi"
        location = "us"
        short_uuid = uuid.uuid4().hex[:12]
        return f"cid_{source}_{location}_{short_uuid}"
