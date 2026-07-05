from pydantic_settings import BaseSettings


class Config(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "My Ai Client Manager"


config: Config = Config()