from typing import Generator
from backend.database import SessionLocal  # Look! Importing the global variable
from fastapi import Security, HTTPException, status, Depends
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session, joinedload
from backend.models.account import Account, APIKeyModel

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def get_db() -> Generator:
    # We call the factory inside a def because we want a FRESH session
    # for every single incoming HTTP request.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_account(
        api_key: str = Security(api_key_header),
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
