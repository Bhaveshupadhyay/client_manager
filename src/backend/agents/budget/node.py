from backend.shared.state import GlobalState
from backend.services.llm_provider import LLmProvider
from backend.agents.budget.tools import BUDGET_TOOLS

class BudgetAgentNode:
    def __init__(self, llm_provider: LLmProvider):
        self.llm = llm_provider

    async def __call__(self, state: GlobalState):
        project_id = state.get("project_id", "Unknown")
        latest_user_message = state["messages"][-1].content

        response = await self.llm.generate_text(
            prompt=str(latest_user_message),
            context_data={"project_id": project_id},
            old_chats=[],
            tools=BUDGET_TOOLS
        )

        return {
            "messages": [response.model_dump_json()],
            "active_agent": "budget"
        }