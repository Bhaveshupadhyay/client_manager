from langchain_core.tools import tool

@tool
def fetch_financial_data(project_id: str) -> dict:
    """Fetch the current budget and estimated cost for the project."""
    # In a real app, this queries your Postgres database
    return {
        "client_budget": 50000,
        "estimated_cost": 45000,
        "status": "under_budget"
    }

@tool
def request_discount_approval(project_id: str, requested_amount: int) -> str:
    """Logs a request for a manager to approve a discount."""
    # Logic to ping a slack channel or update DB
    return f"Discount of ${requested_amount} has been sent to management for review."

# We bundle them into a list to easily pass to the LLM
BUDGET_TOOLS = [fetch_financial_data, request_discount_approval]