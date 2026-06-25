from enum import StrEnum


from pydantic import BaseModel, Field
from typing import Literal

class Timeline(BaseModel):
    count: int = Field(description="The numeric value of the time period")
    type: Literal["days", "weeks", "months", "years"] = Field(description="The unit of time")

class IntentType(StrEnum):
    UPDATE_BUDGET = "update_budget"
    UPDATE_ESTIMATED_COST = "update_estimated_cost"
    RESET_REQUIREMENTS = "reset_requirements"
    UPDATE_TECH_STACK = "update_tech_stack"
    GENERAL_FAQ = "general_faq"

class ClientIntent(BaseModel):
    intent_type: str = Field(description="Must be either 'save_lead' or 'general_faq'")
    text: str = Field(description="Answer the question")
    budget: str | None = None
    timeline: Timeline | None = None
    requirements: str | None = None
    reply_needed: bool = Field(description="True if it's a general question needing an answer right away")