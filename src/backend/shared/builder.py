from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from backend.shared.state import GlobalState
from backend.services.llm_provider import GeminiLLmProvider
from backend.shared.constants import RouteAction

# Import class-based nodes
from backend.agents.budget.node import BudgetAgentNode
from backend.agents.supervisor.node import SupervisorNode
from backend.agents.project_verification.node import ProjectVerificationNode

from backend.core.client import get_cosmos_client
from backend.core.config import config
from backend.repository.project_repository import ProjectRepository

# 1. Instantiate shared dependencies once
# Swapping models is easy from here without touching node implementations
gemini_flash_client = GeminiLLmProvider(model_name="gemini-3.1-flash-lite")

cosmos_client = get_cosmos_client()
database = cosmos_client.get_database_client(config.COSMOS_DATABASE)
container = database.get_container_client("project_requirements")
project_repository = ProjectRepository(cosmos_db_container=container)

# 2. Instantiate agent nodes, injecting the dependency via the constructor
budget_node = BudgetAgentNode(llm_provider=gemini_flash_client, project_repository=project_repository)
supervisor_node = SupervisorNode(llm_provider=gemini_flash_client)
project_verification_node = ProjectVerificationNode(project_repository=project_repository, llm_provider=gemini_flash_client)

# 3. Define state-driven router function
def route_from_supervisor(state: GlobalState) -> str:
    """
    Decides where to route next based on the supervisor node's evaluation
    of user intent stored in `next_action`.
    """
    if state.next_action == RouteAction.BUDGET:
        return "to_budget"
    elif state.next_action == RouteAction.REQUIREMENTS:
        return "to_requirements"
    elif state.next_action == RouteAction.PROJECT_VERIFICATION:
        return "to_project_verification"
    else:
        return "end_conversation"

# 4. Build the StateGraph
builder = StateGraph(GlobalState)

# Add nodes (objects containing __call__ method)
builder.add_node(RouteAction.SUPERVISOR, supervisor_node)
builder.add_node(RouteAction.BUDGET, budget_node)
builder.add_node(RouteAction.PROJECT_VERIFICATION, project_verification_node)

# Entry point starts with the supervisor
builder.add_edge(START, RouteAction.SUPERVISOR)

# Define routing conditional paths
builder.add_conditional_edges(
    RouteAction.SUPERVISOR,
    route_from_supervisor,
    {
        "to_budget": RouteAction.BUDGET,
        # Route requirements to END placeholder until the requirements node is implemented
        "to_requirements": END,
        "to_project_verification": RouteAction.PROJECT_VERIFICATION,
        "end_conversation": END
    }
)

# Hand control back to supervisor after agent runs complete
builder.add_edge(RouteAction.BUDGET, RouteAction.SUPERVISOR)
builder.add_edge(RouteAction.PROJECT_VERIFICATION, RouteAction.SUPERVISOR)

# 5. Compile with session checkpointer for conversation memory
app = builder.compile(checkpointer=MemorySaver())