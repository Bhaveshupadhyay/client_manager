from functools import lru_cache
from typing import Generator
from backend.client import get_postgres_client, get_cosmos_client, get_redis_client, get_qdrant_client
from fastapi import Security, HTTPException, status, Depends,Header,Request
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session, joinedload
from backend.models.account import Account, APIKeyModel
from backend.services.chat_service import ChatService
from backend.services.file_service import FileService
from backend.services.llm_provider import LLmProvider, GeminiLLmProvider
from backend.services.project_service import ProjectService

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def get_db() -> Generator:
    session_local = get_postgres_client()
    db = session_local()
    try:
        yield db
    finally:
        db.close()


def get_client_project_container():
    try:
        cosmos_client = get_cosmos_client()
        database = cosmos_client.get_database_client('ai-client-manager')
        container = database.get_container_client("project_requirements")
        return container
    finally:
        pass

def get_llm_provider() -> LLmProvider:
    return GeminiLLmProvider()

@lru_cache
def get_project_service() -> ProjectService:
    db_container = get_client_project_container()
    return ProjectService(db_container=db_container)

@lru_cache
def get_chat_service() -> ChatService:
    redis_client = get_redis_client()

    return ChatService(redis_client=redis_client)

def get_file_service() -> FileService:
    return FileService(qdrant_client=get_qdrant_client(),llm_provider=get_llm_provider())

def get_current_account(
        api_key: str = Security(api_key_header),
        source: str | None = None,
        db: Session = Depends(get_db)
) -> Account:
    """
    Unified Authentication Dependency.
    Extracts the API key from the headers and retrieves the owner's Account.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: X-API-Key header is missing.",
        )

    api_key_obj = ((db.query(APIKeyModel).options(joinedload(APIKeyModel.account)).
                    filter(APIKeyModel.key_string == api_key))
                   .first())

    if not api_key_obj:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    if not api_key_obj.is_active:
        raise HTTPException(status_code=403, detail="API Key is deactivated")

    return api_key_obj.account
