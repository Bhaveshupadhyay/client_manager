import logging

from backend.models.client import ProjectItem
from backend.models.llm import IntentType, LLMResponse
from backend.repository.project_repository import ProjectRepository
logger = logging.getLogger(__name__)

class ProjectService:
    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    async def project_agent(self, project_id:str|None, llm_response:LLMResponse):
        try:
            intent_type: IntentType= IntentType(llm_response.intent_type.lower())
            if intent_type == IntentType.UPDATE_BUDGET and project_id:
                await self.update_project_budget(project_id=project_id,new_budget=int(llm_response.budget or 0))

            elif intent_type == IntentType.UPDATE_ESTIMATED_COST and project_id:
                #TODO: need estimated cost
                await self.update_project_cost(project_id=project_id,cost=int(llm_response.budget or 0))

            elif intent_type==IntentType.FOUND_PROJECT_ID:
                if llm_response.project_id:
                    project_details= await self.project_repository.get_project_details(project_id=llm_response.project_id)
                    


        except Exception as e:
            raise e



    async def update_project_budget(self, project_id:str,new_budget: int,):

        try:
            project_item = await self.project_repository.get_project_details(project_id)
            if project_item:
                project_item.extracted_facts.client_budget = new_budget

                await self.project_repository.update_project(project_item)

        except Exception as e:
            raise e

    async def update_project_cost(self,project_id:str,cost: int):

        try:
            project_item = await self.project_repository.get_project_details(project_id)
            if project_item:
                project_item.extracted_facts.estimated_cost = cost

                await self.project_repository.update_project(project_item)

        except Exception as e:
            raise e