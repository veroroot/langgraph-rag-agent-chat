"""User CRUD operations."""
import bcrypt
from sqlmodel import Session, select
from backend.models.user import User, UserCreate


def get_user_by_email(session: Session, email: str) -> User | None:
    """Get user by email."""
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def get_user_by_id(session: Session, user_id: int) -> User | None:
    """Get user by ID."""
    return session.get(User, user_id)


def create_user(session: Session, user_create: UserCreate) -> User:
    """Create a new user."""
    hashed_password = bcrypt.hashpw(
        user_create.password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")
    user = User(
        email=user_create.email,
        hashed_password=hashed_password,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )



