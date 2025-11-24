"""Base model for all database tables."""
from sqlmodel import SQLModel
from datetime import datetime
from typing import Optional


class TimestampMixin(SQLModel):
    """Mixin for created_at and updated_at timestamps."""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None



