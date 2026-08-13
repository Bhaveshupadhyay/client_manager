from langchain_core.messages import AIMessage
from backend.shared.state import GlobalState
from backend.services.llm_provider import LLmProvider
from backend.agents.requirements.prompt import REQUIREMENTS_SYSTEM_PROMPT
from backend.shared.constants import RouteAction

class RequirementsAgentNode:
    def __init__(self, llm_provider: LLmProvider):
        self.llm = llm_provider

    async def __call__(self, state: GlobalState):
        project_id = state.project_id or "Unknown"
        latest_user_message = state.messages[-1].content if state.messages else ""

        system_instruction = REQUIREMENTS_SYSTEM_PROMPT.format(project_id=project_id)

        response = await self.llm.generate_text(
            prompt=str(latest_user_message),
            context_data={"project_id": project_id},
            old_chats=[],
            system_instruction=system_instruction
        )


        updates = GlobalState(
            messages=[AIMessage(content=response.text)],
            active_agent=RouteAction.REQUIREMENTS
        )
        
        if response.requirements:
            updates.requirements_list = [response.requirements]
            
        return updates.get_updates()
