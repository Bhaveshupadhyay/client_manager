from functools import lru_cache
from typing import Generator
from backend.core.config import config
from backend.core.client import get_postgres_client, get_cosmos_client, get_redis_client, get_qdrant_client
from fastapi import Security, HTTPException, status, Depends
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session, joinedload
from backend.models.account import Account, APIKeyModel
from backend.repository.chat_repository import ChatRepository
from backend.repository.file_repository import FileRepository
from backend.repository.project_repository import ProjectRepository
from backend.services.chat_service import ChatService
from backend.services.embeddings_provider import SparseEmbeddingsProvider,DenseEmbeddingsProvider, GeminiDenseEmbeddingsProvider, HuggingFaceProviderSparse
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
        database = cosmos_client.get_database_client(config.COSMOS_DATABASE)
        container = database.get_container_client("project_requirements")
        return container
    finally:
        pass

def get_llm_provider() -> LLmProvider:
    return GeminiLLmProvider()

def get_sparse_embedding_provider() -> SparseEmbeddingsProvider:
    return HuggingFaceProviderSparse()

def get_dense_embedding_provider() -> DenseEmbeddingsProvider:
    return GeminiDenseEmbeddingsProvider()

@lru_cache
def get_project_service() -> ProjectService:
    return ProjectService(project_repository=get_project_repository())

@lru_cache
def get_chat_service() -> ChatService:
    return ChatService(project_service=get_project_service(),
                       project_repository=get_project_repository(),
                       chat_repository=get_chat_repository(),
                       llm_provider=get_llm_provider(),
                       )

@lru_cache
def get_file_service() -> FileService:
    return FileService(file_repository=get_file_repository())

def get_chat_repository() -> ChatRepository:
    return ChatRepository(redis_client=get_redis_client())

def get_project_repository() -> ProjectRepository:
    db_container = get_client_project_container()
    return ProjectRepository(cosmos_db_container=db_container)

def get_file_repository() -> FileRepository:
    return FileRepository(qdrant_client=get_qdrant_client(),
                          dense_embedding_provider=get_dense_embedding_provider(),
                          sparse_embeddings_provider=get_sparse_embedding_provider(),
                          collection_name="client_conversations")


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
