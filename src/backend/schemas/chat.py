from enum import Enum
from typing import Optional
from pydantic import BaseModel


class ClientActionType(str, Enum):
    """Actions the frontend sends TO the backend"""
    START_NEW_PROJECT = "start_new_project"
    CONTINUE_PROJECT = "continue_project"

class ServerActionType(str, Enum):
    """Actions the backend sends TO the frontend UI"""
    START_NEW_PROJECT = "start_new_project"


class ChatRequest(BaseModel):
    message: str
    client_name: str
    project_id: Optional[str] = None
    action_type: Optional[ClientActionType] = None


class ChatResponse(BaseModel):
    message: str
    name: str
    action: Optional[ServerActionType] = None
    project_id: Optional[str] = None


class ChatMessage(BaseModel):
    role: str
    text: str
