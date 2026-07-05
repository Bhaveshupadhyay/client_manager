from fastapi import APIRouter, Depends, HTTPException, status
from backend.schemas.user import UserLogin, TokenResponse
from backend.services.auth_service import authenticate_user
from backend.core.security import create_access_token
from backend.core.dependencies import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db=Depends(get_db)):
    # 1. Call the business logic layer to check credentials
    user = authenticate_user(db, email=payload.email, password=payload.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    token = create_access_token(data={"sub": user.email})

    return {"access_token": token, "token_type": "bearer"}
