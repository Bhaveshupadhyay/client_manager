from enum import StrEnum

from pydantic import BaseModel, Field


class RouteAction(StrEnum):
    BUDGET = "budget"
    REQUIREMENTS = "requirements"
    ESTIMATION = "estimation"
    PROJECT_VERIFICATION = "project_verification"
    SUPERVISOR = "supervisor"
    END = "END"

class RouterDecision(BaseModel):
    next_action: RouteAction = Field(
        description="The next action or agent to route the conversation to."
    )