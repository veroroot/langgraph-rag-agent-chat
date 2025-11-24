"""User service for authentication and user management."""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from sqlmodel import Session
from backend.core.config import settings
from backend.crud import user_crud
from backend.models.user import User, UserCreate, UserLogin, Token


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def authenticate_user(session: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password."""
    user = user_crud.get_user_by_email(session, email)
    if not user:
        return None
    if not user_crud.verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


def register_user(session: Session, user_create: UserCreate) -> User:
    """Register a new user."""
    # Check if user already exists
    existing_user = user_crud.get_user_by_email(session, user_create.email)
    if existing_user:
        raise ValueError("User with this email already exists")
    
    return user_crud.create_user(session, user_create)


def login_user(session: Session, user_login: UserLogin) -> Token:
    """Login user and return access token."""
    user = authenticate_user(session, user_login.email, user_login.password)
    if not user:
        raise ValueError("Invalid email or password")
    
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return Token(access_token=access_token, token_type="bearer")


def get_current_user(session: Session, token: str) -> Optional[User]:
    """Get current user from JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    
    user = user_crud.get_user_by_id(session, int(user_id))
    return user



