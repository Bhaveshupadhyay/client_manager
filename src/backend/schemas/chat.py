from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    client_name: str



class ChatResponse(BaseModel):
    message: str
    name: str
    action: Optional[str] = None


class ChatMessage(BaseModel):
    role: str
    text: str
