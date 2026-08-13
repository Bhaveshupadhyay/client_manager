from langchain_core.messages import AIMessage
from backend.shared.state import GlobalState
from backend.services.llm_provider import LLmProvider
from backend.repository.project_repository import ProjectRepository
from backend.agents.budget.tools import get_budget_tools
from backend.agents.budget.prompt import BUDGET_SYSTEM_PROMPT
from backend.shared.constants import RouteAction

class BudgetAgentNode:
    def __init__(self, llm_provider: LLmProvider, project_repository: ProjectRepository):
        self.llm = llm_provider
        self.project_repository = project_repository

    async def __call__(self, state: GlobalState):
        project_id = state.project_id or "Unknown"
        latest_user_message = state.messages[-1].content if state.messages else ""

        tools = get_budget_tools(self.project_repository)
        system_instruction = BUDGET_SYSTEM_PROMPT.format(project_id=project_id)

        response = await self.llm.generate_text(
            prompt=str(latest_user_message),
            context_data={"project_id": project_id},
            old_chats=[],
            tools=tools,
            system_instruction=system_instruction
        )

        updates = GlobalState(
            messages=[AIMessage(content=response.text)],
            active_agent=RouteAction.BUDGET
        )
        try:
            if response.budget:
                updates.client_budget = float(response.budget)
        except (ValueError, TypeError):
            updates.client_budget = None
        
        return updates.get_updates()