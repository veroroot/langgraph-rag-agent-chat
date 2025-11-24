"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session
from backend.core.db import get_session
from backend.models.user import UserCreate, UserLogin, Token, UserRead
from backend.services.user_service import register_user, login_user, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_active_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> UserRead:
    """Get current active user from JWT token."""
    user = get_current_user(session, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return UserRead.model_validate(user)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    session: Session = Depends(get_session),
):
    """Register a new user."""
    try:
        user = register_user(session, user_create)
        return UserRead.model_validate(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    """Login and get access token."""
    user_login = UserLogin(email=form_data.username, password=form_data.password)
    try:
        token = login_user(session, user_login)
        return token
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserRead)
async def get_me(current_user: UserRead = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user



