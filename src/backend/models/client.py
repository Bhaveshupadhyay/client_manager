from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime, timezone

class Requirement(BaseModel):
    text: str
    vector: List[float]

class ExtractedFacts(BaseModel):
    client_budget: int
    estimated_cost: float = 0.0
    currency: str = "USD"
    tech_stack: List[str] = Field(default_factory=list)
    agreed_requirements: List[Requirement] = Field(default_factory=list)

class ProjectItem(BaseModel):
    id: str
    client_id: str
    project_id: str
    type: Literal["profile_metadata"] = "profile_metadata"
    extracted_facts: ExtractedFacts

    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))