import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Config(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "My Ai Client Manager"
    HUGGING_FACE_USER_NAME: str = os.getenv("HUGGING_FACE_USER_NAME")
    HUGGING_FACE_SPACE: str = os.getenv("HUGGING_FACE_SPACE")
    HUGGING_FACE_TOKEN: str = os.getenv("HUGGING_FACE_TOKEN")


config: Config = Config()