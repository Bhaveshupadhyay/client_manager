# app/services/user.py
from sqlalchemy.orm import Session
from backend.models.user import UserModel
from backend.core.security import verify_password  # Your password hashing helper


def authenticate_user(db: Session, email: str, password: str):
    # 1. Look up the user in the database by their email
    # (UserModel comes from app/models/user.py)
    user = db.query(UserModel).filter(UserModel.email == email).first()

    # 2. If the user doesn't exist, return None immediately
    if not user:
        return None

    # 3. Check if the password they typed matches the hashed_password in the DB
    # (verify_password will return True or False)
    if not verify_password(password, user.hashed_password):
        return None

    # 4. If the user is deactivated/banned, you can handle that here too
    if not user.is_active:
        return None

    # 5. Success! Return the user database object
    return user
