import os
from typing import Generator

from azure.cosmos.aio import CosmosClient, DatabaseProxy

from backend.database import SessionLocal  # Look! Importing the global variable
from fastapi import Security, HTTPException, status, Depends,Header,Request
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session, joinedload
from backend.models.account import Account, APIKeyModel
from backend.services.llm_provider import LLmProvider, GeminiLLmProvider

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_cosmos_db(request: Request) -> DatabaseProxy:
    try:
        database = request.app.state.cosmos_db
        return database
    finally:
        pass

def get_client_project_container(request: Request) -> Generator:
    try:
        cosmos_db = get_cosmos_db(request)
        container = cosmos_db.get_container_client("project_requirements")
        yield container
    finally:
        pass

def get_llm_provider() -> LLmProvider:
    return GeminiLLmProvider()

async def get_redis(request: Request) -> Generator:
    return request.app.state.redis

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

    # Query your PostgreSQL accounts table using the high-performance index we set up
    api_key_obj = ((db.query(APIKeyModel).options(joinedload(APIKeyModel.account)).
                    filter(APIKeyModel.key_string == api_key))
                   .first())

    if not api_key_obj:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    # 3. Check if the key is active
    if not api_key_obj.is_active:
        raise HTTPException(status_code=403, detail="API Key is deactivated")

    return api_key_obj.account
