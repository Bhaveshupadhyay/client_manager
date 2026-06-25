from azure.cosmos import exceptions
import datetime

from azure.cosmos.aio import ContainerProxy
from fastapi import HTTPException

from backend.models.client import ProjectItem, ExtractedFacts


async def update_or_create_project_budget(project_id: str, client_id:str, new_budget: int, db_container: ContainerProxy):

    item_id = project_id

    try:
        existing_item = await db_container.read_item(
            item=item_id,
            partition_key=project_id
        )

        # UPDATE THE BUDGET
        existing_item["extracted_facts"]["client_budget"] = new_budget
        existing_item["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"

        # SAVE THE UPDATED ITEM
        await db_container.replace_item(
            item=item_id,
            body=existing_item
        )
        return {"status": "updated", "budget": new_budget}

    except exceptions.CosmosResourceNotFoundError:
        new_project = ProjectItem(
            id=item_id,
            client_id=client_id,
            project_id=project_id,
            extracted_facts=ExtractedFacts(
                client_budget=new_budget
            )
        )

        try:
            await db_container.create_item(body=new_project.model_dump(mode="json"))
            return {"status": "created", "budget": new_budget}

        except exceptions.CosmosResourceExistsError:
            raise HTTPException(
                status_code=409,
                detail="Project was created by another process. Please try updating again."
            )

        except exceptions.CosmosHttpResponseError as e:

            if e.status_code == 429:
                raise HTTPException(status_code=429, detail="Database is currently overloaded. Please try again later.")

            raise HTTPException(status_code=500, detail="An internal database error occurred.")


async def get_project_details(project_id: str, db_container: ContainerProxy) -> ProjectItem:
    item_id = project_id

    try:
        existing_item = await db_container.read_item(
            item=item_id,
            partition_key=project_id
        )
        return ProjectItem.model_validate(existing_item)

    except Exception as e:
        raise




