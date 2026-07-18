from langgraph.graph import StateGraph, START
from backend.shared.state import GlobalState

# Import your concrete LLM provider
from backend.services.llm_provider import GeminiLLmProvider

# Import your class-based nodes
from backend.agents.budget.node import BudgetAgentNode
# from backend.agents.requirements.node import RequirementsAgentNode

# 1. Instantiate your dependencies ONCE
# If you are closely monitoring backend latency for app performance,
# you could easily swap this out for a faster model implementation here without touching the node code.
gemini_flash_client = GeminiLLmProvider(model_name="gemini-3.1-flash-lite")

# 2. Instantiate your nodes, injecting the dependency via the constructor
budget_node = BudgetAgentNode(llm_provider=gemini_flash_client)
# requirements_node = RequirementsAgentNode(llm_provider=gemini_flash_client)

# 3. Build the graph
builder = StateGraph(GlobalState)

# Because BudgetAgentNode has a __call__ method, LangGraph accepts the object directly
builder.add_node("budget", budget_node)
builder.add_node("supervisor", supervisor_node)
# builder.add_node("requirements", requirements_node)

builder.add_edge(START, "budget")
builder.add_conditional_edges(
    "supervisor",
    route_from_supervisor,
    {
        "to_requirements": "requirements",
        "to_budget": "budget",
        "end_conversation": END
    }
)

app = builder.compile()