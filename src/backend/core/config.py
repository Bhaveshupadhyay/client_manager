from pydantic_settings import BaseSettings


class Config(BaseSettings):
    API_V1_STR: str = "/api/v1"