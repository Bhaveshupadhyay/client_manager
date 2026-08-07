from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "My Ai Client Manager"
    
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    POSTGRES_DB_USER: str = ""
    POSTGRES_DB_PASSWORD: str = ""
    POSTGRES_DB_HOST: str = ""
    POSTGRES_DB_NAME: str = ""
    POSTGRES_DB_PORT: str = "5432"
    
    COSMOS_ENDPOINT: str | None = None
    COSMOS_KEY: str | None = None
    COSMOS_DATABASE: str = ""
    
    GEMINI_API_KEY: str | None = None
    
    AZURE_REDIS_ENDPOINT: str | None = None
    AZURE_REDIS_KEY: str | None = None
    
    UPSTASH_REDIS_REST_URL: str | None = None
    UPSTASH_REDIS_REST_TOKEN: str | None = None
    
    QDRANT_ENDPOINT: str | None = None
    QDRANT_KEY: str | None = None
    
    HUGGING_FACE_USER_NAME: str = ""
    HUGGING_FACE_SPACE: str = ""
    HUGGING_FACE_TOKEN: str = ""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

config: Config = Config()