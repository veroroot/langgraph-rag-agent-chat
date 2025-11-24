"""Chat CRUD operations."""
from sqlmodel import Session, select
from typing import Optional, List
from datetime import datetime
from backend.models.chat import ChatSession, ChatMessage, ChatSessionCreate, ChatMessageCreate


def create_chat_session(session: Session, user_id: int, session_create: Optional[ChatSessionCreate] = None) -> ChatSession:
    """Create a new chat session."""
    chat_session = ChatSession(
        user_id=user_id,
        title=session_create.title if session_create else None,
    )
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)
    return chat_session


def get_chat_session_by_id(session: Session, session_id: int) -> Optional[ChatSession]:
    """Get chat session by ID."""
    return session.get(ChatSession, session_id)


def get_chat_sessions_by_user(session: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[ChatSession]:
    """Get chat sessions by user."""
    statement = (
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def create_chat_message(session: Session, message_create: ChatMessageCreate) -> ChatMessage:
    """Create a new chat message."""
    chat_message = ChatMessage(
        session_id=message_create.session_id,
        role=message_create.role,
        content=message_create.content,
    )
    session.add(chat_message)
    
    # Update session updated_at
    chat_session = session.get(ChatSession, message_create.session_id)
    if chat_session:
        chat_session.updated_at = datetime.utcnow()
        session.add(chat_session)
    
    session.commit()
    session.refresh(chat_message)
    return chat_message


def get_messages_by_session(session: Session, session_id: int, limit: int = 100) -> List[ChatMessage]:
    """Get messages by session ID."""
    statement = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    return list(session.exec(statement).all())


def update_chat_session(session: Session, session_id: int, title: Optional[str] = None) -> Optional[ChatSession]:
    """Update a chat session."""
    chat_session = session.get(ChatSession, session_id)
    if not chat_session:
        return None
    
    if title is not None:
        chat_session.title = title
        chat_session.updated_at = datetime.utcnow()
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)
    
    return chat_session


def delete_chat_session(session: Session, session_id: int) -> bool:
    """Delete chat session and all messages."""
    chat_session = session.get(ChatSession, session_id)
    if not chat_session:
        return False
    
    # Delete all messages first
    messages = get_messages_by_session(session, session_id, limit=10000)
    for message in messages:
        session.delete(message)
    
    session.delete(chat_session)
    session.commit()
    return True



