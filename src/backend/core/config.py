from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

from enum import Enum

class CosmosContainers(str, Enum):
    AGENT_INTERACTIONS = "AgentInteractions"
    PROJECT_REQUIREMENTS = "project_requirements"