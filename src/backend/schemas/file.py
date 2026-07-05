from pydantic import BaseModel


class FileCheckResponse(BaseModel):
    exists: bool
    message: str