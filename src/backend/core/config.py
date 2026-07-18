import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Config(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "My Ai Client Manager"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    POSTGRES_DB_USER: str = os.getenv("POSTGRES_DB_USER", "")
    POSTGRES_DB_PASSWORD: str = os.getenv("POSTGRES_DB_PASSWORD", "")
    POSTGRES_DB_HOST: str = os.getenv("POSTGRES_DB_HOST", "")
    POSTGRES_DB_NAME: str = os.getenv("POSTGRES_DB_NAME", "")
    
    COSMOS_ENDPOINT: str | None = os.getenv("COSMOS_ENDPOINT")
    COSMOS_KEY: str | None = os.getenv("COSMOS_KEY")
    COSMOS_DATABASE: str = os.getenv("COSMOS_DATABASE", "")
    
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    
    AZURE_REDIS_ENDPOINT: str | None = os.getenv("AZURE_REDIS_ENDPOINT")
    AZURE_REDIS_KEY: str | None = os.getenv("AZURE_REDIS_KEY")
    
    UPSTASH_REDIS_REST_URL: str | None = os.getenv("UPSTASH_REDIS_REST_URL")
    UPSTASH_REDIS_REST_TOKEN: str | None = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    
    QDRANT_ENDPOINT: str | None = os.getenv("QDRANT_ENDPOINT")
    QDRANT_KEY: str | None = os.getenv("QDRANT_KEY")
    
    HUGGING_FACE_USER_NAME: str = os.getenv("HUGGING_FACE_USER_NAME", "")
    HUGGING_FACE_SPACE: str = os.getenv("HUGGING_FACE_SPACE", "")
    HUGGING_FACE_TOKEN: str = os.getenv("HUGGING_FACE_TOKEN", "")


config: Config = Config()