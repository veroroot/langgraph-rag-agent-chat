"""Chat model for conversation history."""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class ChatSessionBase(SQLModel):
    """Base chat session schema."""
    title: Optional[str] = None


class ChatSession(ChatSessionBase, table=True):
    """Chat session database model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class ChatMessageBase(SQLModel):
    """Base chat message schema."""
    role: str  # user, assistant, system
    content: str


class ChatMessage(ChatMessageBase, table=True):
    """Chat message database model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chatsession.id")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class ChatSessionCreate(SQLModel):
    """Schema for creating a chat session."""
    title: Optional[str] = None


class ChatSessionUpdate(SQLModel):
    """Schema for updating a chat session."""
    title: Optional[str] = None


class ChatSessionRead(ChatSessionBase):
    """Schema for reading chat session data."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class ChatMessageCreate(SQLModel):
    """Schema for creating a chat message."""
    role: str
    content: str
    session_id: Optional[int] = None  # If None, create new session


class ChatMessageRead(ChatMessageBase):
    """Schema for reading chat message data."""
    id: int
    session_id: int
    created_at: datetime


class ChatRequest(SQLModel):
    """Schema for chat request."""
    message: str
    session_id: Optional[int] = None
    stream: bool = False
    provider: Optional[str] = None  # Optional provider name (e.g., 'openai', 'anthropic')
    model: Optional[str] = None  # Optional model name, uses default if not provided


class ChatResponse(SQLModel):
    """Schema for chat response."""
    message: str
    session_id: int
    sources: Optional[list[dict]] = None  # Retrieved document sources


class Message(SQLModel):
    """Simple message model for agent communication (not a database model).
    
    This is used for passing messages between services and the LangGraph agent.
    For database operations, use ChatMessage instead.
    """
    role: str  # user, assistant, system
    content: str



