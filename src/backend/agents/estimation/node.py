from langchain_core.messages import AIMessage
from backend.shared.state import GlobalState
from backend.services.llm_provider import LLmProvider
from backend.agents.estimation.prompt import ESTIMATION_SYSTEM_PROMPT
from backend.shared.constants import RouteAction

class EstimationAgentNode:
    def __init__(self, llm_provider: LLmProvider):
        self.llm = llm_provider

    async def __call__(self, state: GlobalState):
        project_id = state.project_id or "Unknown"
        latest_user_message = state.messages[-1].content if state.messages else ""

        # Format requirements as a readable string
        requirements_str = "\n".join(f"- {req}" for req in state.requirements_list) if state.requirements_list else "No requirements gathered yet."

        system_instruction = ESTIMATION_SYSTEM_PROMPT.format(
            project_id=project_id,
            requirements_list=requirements_str
        )

        response = await self.llm.generate_text(
            prompt=str(latest_user_message),
            context_data={"project_id": project_id},
            old_chats=[],
            system_instruction=system_instruction
        )

        updates = GlobalState(
            messages=[AIMessage(content=response.text)],
            active_agent=RouteAction.ESTIMATION
        )
        
        try:
            if response.budget:
                updates.estimated_cost = float(response.budget)
        except (ValueError, TypeError):
            pass

        return updates.get_updates()
