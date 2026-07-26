from enum import Enum
from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    client_name: str
    project_id: Optional[str] = None


class ActionType(str, Enum):
    START_NEW_PROJECT = "start_new_project"
    CONTINUE_PROJECT = "continue_project"


class ChatResponse(BaseModel):
    message: str
    name: str
    action: Optional[ActionType] = None
    project_id: Optional[str] = None


class ChatMessage(BaseModel):
    role: str
    text: str
