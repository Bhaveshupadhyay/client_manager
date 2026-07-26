import logging
from langchain_core.messages import AIMessage, HumanMessage
from backend.shared.state import GlobalState
from backend.services.llm_provider import LLmProvider
from backend.agents.supervisor.prompt import SUPERVISOR_SYSTEM_PROMPT
from backend.shared.constants import RouteAction, RouterDecision

logger = logging.getLogger(__name__)

class SupervisorNode:
    def __init__(self, llm_provider: LLmProvider):
        self.llm_provider = llm_provider

    async def __call__(self, state: GlobalState):
        # 1. If the last message in state is already an AI message,
        # it means a worker node just finished generating a response. Route directly to END.
        print(state.messages[-1].content)
        if state.messages and isinstance(state.messages[-1], AIMessage):
            updates = GlobalState(next_action=RouteAction.END)
            return updates.get_updates()

        gemini_content = []
        if state.messages:
            for msg in state.messages:
                role = "user" if isinstance(msg, HumanMessage) else "model"
                gemini_content.append({
                    "role": role,
                    "parts": [{"text": msg.content}]
                })
        else:
            updates = GlobalState(next_action=RouteAction.END)
            return updates.get_updates()

        try:
            decision = await self.llm_provider.generate_structured(
                prompt=gemini_content,
                response_schema=RouterDecision,
                system_instruction=SUPERVISOR_SYSTEM_PROMPT,
                temperature=0.1
            )
            next_action = decision.next_action
        except Exception as e:
            logger.warning(f"Supervisor failed to generate structured routing, falling back to END: {e}")
            next_action = RouteAction.END

        updates = GlobalState(next_action=next_action)

        # 2. If the supervisor decides to end immediately without calling a specialized agent
        # (e.g. for general FAQ or greetings), generate the fallback response text here.
        if next_action == RouteAction.END:
            # Call the default LLM provider text generator to handle general conversation
            fallback_response = await self.llm_provider.generate_text(
                prompt=str(state.messages[-1].content),
                context_data={"project_id": state.project_id or "Unknown"},
                old_chats=[]
            )
            updates.messages = [AIMessage(content=fallback_response.text)]

        return updates.get_updates()
