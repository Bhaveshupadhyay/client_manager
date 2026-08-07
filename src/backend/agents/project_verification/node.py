from langchain_core.messages import AIMessage

from backend.schemas.chat import ServerActionType
from backend.shared.state import GlobalState
from backend.repository.project_repository import ProjectRepository
from backend.agents.project_verification.prompt import PROJECT_VERIFICATION_SYSTEM_PROMPT
from backend.shared.constants import RouteAction

class ProjectVerificationNode:
    def __init__(self, project_repository: ProjectRepository, llm_provider):
        self.project_repository = project_repository
        self.llm = llm_provider

    async def __call__(self, state: GlobalState):
        latest_user_message = state.messages[-1].content if state.messages else ""

        # 1. Use the LLM to extract the project ID from the conversation
        response = await self.llm.generate_text(
            prompt=str(latest_user_message),
            context_data={},
            old_chats=[],
            system_instruction=PROJECT_VERIFICATION_SYSTEM_PROMPT
        )

        project_id = response.project_id

        if not project_id:
            text_reply = response.text or "Could you please specify your project ID?"
            updates = GlobalState(
                messages=[AIMessage(content=text_reply)],
                active_agent=RouteAction.PROJECT_VERIFICATION
            )
            return updates.get_updates()

        # 2. Check Cosmos DB for project details
        project_details = await self.project_repository.get_project_details(project_id)
        
        if project_details:
            client_budget = None
            estimated_cost = None
            if project_details.extracted_facts:
                client_budget = project_details.extracted_facts.client_budget
                estimated_cost = project_details.extracted_facts.estimated_cost

            updates = GlobalState(
                project_id=project_id,
                client_budget=client_budget,
                estimated_cost=estimated_cost,
                messages=[AIMessage(content=f"Successfully verified project ID: {project_id}. I have loaded your project details.")],
                active_agent=RouteAction.PROJECT_VERIFICATION
            )
            return updates.get_updates()
        else:
            updates = GlobalState(
                project_id=project_id,
                messages=[AIMessage(content=f"We couldn't find project ID '{project_id}' in our database. You can find the project ID in the invoice we sent you from clientmanager.tech, or if you'd like we can start a new project!")],
                active_agent=RouteAction.PROJECT_VERIFICATION,
                action=ServerActionType.START_NEW_PROJECT
            )
            return updates.get_updates()
