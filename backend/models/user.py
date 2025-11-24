"""User model."""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class UserBase(SQLModel):
    """Base user schema."""
    email: str = Field(unique=True, index=True)
    is_active: bool = True
    is_admin: bool = False


class User(UserBase, table=True):
    """User database model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class UserCreate(SQLModel):
    """Schema for creating a user."""
    email: str
    password: str


class UserRead(UserBase):
    """Schema for reading user data."""
    id: int
    created_at: datetime
    updated_at: datetime


class UserLogin(SQLModel):
    """Schema for user login."""
    email: str
    password: str


class Token(SQLModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"



