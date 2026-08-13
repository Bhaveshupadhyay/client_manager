from langchain_core.tools import tool
from backend.repository.project_repository import ProjectRepository

def get_budget_tools(project_repository: ProjectRepository) -> list:
    @tool
    async def fetch_financial_data(project_id: str) -> dict:
        """Fetch the current budget and estimated cost for the project."""
        project = await project_repository.get_project_details(project_id)
        
        if not project:
            return {
                "client_budget": 0,
                "estimated_cost": 0,
                "status": "not_found"
            }
            
        budget = project.extracted_facts.client_budget
        cost = project.extracted_facts.estimated_cost
        
        # Determine if project is under or over budget
        status = "under_budget" if budget >= cost else "over_budget"
        
        return {
            "client_budget": budget,
            "estimated_cost": cost,
            "status": status
        }

    @tool
    def request_discount_approval(project_id: str, requested_amount: int) -> str:
        """Logs a request for a manager to approve a discount."""
        # Logic to ping a slack channel or update DB
        return f"Discount of ${requested_amount} has been sent to management for review."

    return [fetch_financial_data, request_discount_approval]