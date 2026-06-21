from typing import Optional

from pydantic import BaseModel, Field


class ClientIntent(BaseModel):
    intent_type: str = Field(description="Must be either 'save_lead' or 'general_faq'")
    text: str = Field(description="Answer the question")
    budget: str | None = None
    timeline: str | None = None
    reply_needed: bool = Field(description="True if it's a general question needing an answer right away")