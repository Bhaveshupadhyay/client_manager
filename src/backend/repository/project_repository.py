import logging
from datetime import datetime, timezone
from typing import Any

from azure.cosmos import exceptions
from fastapi import HTTPException
from azure.cosmos.aio import ContainerProxy
from pydantic import ValidationError

from backend.models.client import ProjectItem
from backend.services.redis_service import cached

logger = logging.getLogger(__name__)


class ProjectRepository:
    def __init__(self,cosmos_db_container: ContainerProxy):
        self.cosmos_db_container = cosmos_db_container
        pass


    @cached(
        namespace="project_requirements",
        redis_ttl=3600,
        return_type=ProjectItem,
        key=['project_id']
    )
    async def get_project_details(self,project_id:str)->ProjectItem | None:
        item_id = project_id

        try:
            existing_item = await self.cosmos_db_container.read_item(
                item=item_id,
                partition_key=project_id
            )
            return ProjectItem.model_validate(existing_item)

        except exceptions.CosmosResourceNotFoundError:
            return None

        except ValidationError as e:
            logger.error(f"Data validation failed for project {project_id}: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error fetching project {project_id} from Cosmos: {e}")
            raise

    async def update_project(self, project_item:ProjectItem):

        item_id = project_item.project_id

        try:
            json= project_item.model_dump()
            json['updated_at'] = datetime.now(timezone.utc).isoformat(timespec='seconds').replace("+00:00", "Z")

            await self.cosmos_db_container.replace_item(
                item=item_id,
                body=json
            )

        except exceptions.CosmosResourceNotFoundError:
            await self.create_project(project_item)


    async def update_single_project_field(self, project_id: str, field_path, new_value: Any):
        """
        Updates a single field in the Cosmos DB document.
        :param project_id: The ID of the project to update.
        :param field_path: A PatchPath from ProjectFields, or a raw JSON Patch path string (must start with '/').
        :param new_value: The new value for the field.
        """
        resolved_path = field_path.path if hasattr(field_path, 'path') else field_path

        try:
            updated_at_str = datetime.now(timezone.utc).isoformat(timespec='seconds').replace("+00:00", "Z")

            await self.cosmos_db_container.patch_item(
                item=project_id,
                partition_key=project_id,
                patch_operations=[
                    {"op": "set", "path": resolved_path, "value": new_value},
                    {"op": "set", "path": "/updated_at", "value": updated_at_str}
                ]
            )
        except exceptions.CosmosResourceNotFoundError:
            logger.error(f"Cannot patch project {project_id} because it does not exist.")
            raise

    async def create_project(self,project_item: ProjectItem,):

        try:
            await self.cosmos_db_container.create_item(body=project_item.model_dump(mode="json"))

        except exceptions.CosmosResourceExistsError:
            raise Exception("Project was created by another process. Please try updating again.")

        except exceptions.CosmosHttpResponseError as e:

            if e.status_code == 429:
                raise HTTPException(status_code=429, detail="Database is currently overloaded. Please try again later.")

            raise HTTPException(status_code=500, detail="An internal database error occurred.")