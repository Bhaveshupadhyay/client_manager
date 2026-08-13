import logging

from backend.models.client import ProjectItem
from backend.models.fields import ProjectFields
from backend.models.llm import IntentType, LLMResponse
from backend.repository.project_repository import ProjectRepository
logger = logging.getLogger(__name__)

class ProjectService:
    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository


    async def update_project_budget(self, project_id: str, new_budget: float):
        await self.project_repository.update_single_project_field(
            project_id=project_id,
            field_path=ProjectFields.extracted_facts.client_budget,
            new_value=new_budget
        )

    async def update_project_cost(self, project_id: str, cost: float):
        project_item = await self.project_repository.get_project_details(project_id)
        if project_item:
            project_item.extracted_facts.estimated_cost = cost
            await self.project_repository.update_project(project_item)