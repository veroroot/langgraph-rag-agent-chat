"""Chat service for handling conversations."""
from typing import Optional, AsyncIterator
import asyncio
from sqlmodel import Session
from backend.crud import chat_crud
from backend.core.config import settings
from backend.models.chat import (
    ChatSession,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatMessageCreate,
)


def create_chat_session(session: Session, user_id: int, title: Optional[str] = None) -> ChatSession:
    """Create a new chat session."""
    session_create = ChatSessionCreate(title=title)
    return chat_crud.create_chat_session(session, user_id, session_create)


def get_chat_history(session: Session, session_id: int) -> list[ChatMessage]:
    """Get chat history for a session."""
    return chat_crud.get_messages_by_session(session, session_id)


async def send_message(
    session: Session,
    user_id: int,
    chat_request: ChatRequest
) -> ChatResponse:
    """Send a message and get agent response."""
    # Get or create chat session
    if chat_request.session_id:
        chat_session = chat_crud.get_chat_session_by_id(session, chat_request.session_id)
        if not chat_session:
            raise ValueError(f"Chat session {chat_request.session_id} not found")
        if chat_session.user_id != user_id:
            raise ValueError("Not authorized to access this chat session")
    else:
        chat_session = create_chat_session(session, user_id)
    
    # Save user message
    user_message = ChatMessageCreate(
        session_id=chat_session.id,
        role="user",
        content=chat_request.message,
    )
    chat_crud.create_chat_message(session, user_message)
    
    # Get chat history for context
    history = get_chat_history(session, chat_session.id)
    chat_history = []
    for msg in history[:-1]:  # Exclude the message we just added
        if msg.role == "user":
            chat_history.append((msg.content, ""))
        elif msg.role == "assistant" and chat_history:
            chat_history[-1] = (chat_history[-1][0], msg.content)
    
    # Query agent based on AGENT_TYPE setting
    session_id_str = str(chat_session.id)
    
    if settings.AGENT_TYPE == "langgraph":
        # Use LangGraph agent
        from backend.services.langgraph_agent import query_agent as langgraph_query_agent
        agent_response = await langgraph_query_agent(
            question=chat_request.message,
            chat_history=chat_history if chat_history else None,
            user_id=user_id,
            session_id=session_id_str,
            provider=chat_request.provider,
            model=chat_request.model,
        )
    else:
        # Use LangChain chain-based agent
        from backend.services.langchain_agent import query_agent as langchain_query_agent
        # langchain_query_agent is sync, so we need to run it in executor
        loop = asyncio.get_event_loop()
        agent_response = await loop.run_in_executor(
            None,
            lambda: langchain_query_agent(
                question=chat_request.message,
                chat_history=chat_history if chat_history else None,
                user_id=user_id,
            )
        )
    
    # Save assistant message
    assistant_message = ChatMessageCreate(
        session_id=chat_session.id,
        role="assistant",
        content=agent_response["answer"],
    )
    chat_crud.create_chat_message(session, assistant_message)
    
    return ChatResponse(
        message=agent_response["answer"],
        session_id=chat_session.id,
        sources=agent_response.get("sources"),
    )


def get_user_chat_sessions(session: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[ChatSession]:
    """Get all chat sessions for a user."""
    return chat_crud.get_chat_sessions_by_user(session, user_id, skip, limit)


def update_chat_session(session: Session, session_id: int, user_id: int, session_update: ChatSessionUpdate) -> ChatSession:
    """Update a chat session."""
    chat_session = chat_crud.get_chat_session_by_id(session, session_id)
    if not chat_session:
        raise ValueError(f"Chat session {session_id} not found")
    
    if chat_session.user_id != user_id:
        raise ValueError("Not authorized to update this chat session")
    
    updated_session = chat_crud.update_chat_session(session, session_id, session_update.title)
    if not updated_session:
        raise ValueError(f"Failed to update chat session {session_id}")
    
    return updated_session


def delete_chat_session(session: Session, session_id: int, user_id: int) -> bool:
    """Delete a chat session."""
    chat_session = chat_crud.get_chat_session_by_id(session, session_id)
    if not chat_session:
        raise ValueError(f"Chat session {session_id} not found")
    
    if chat_session.user_id != user_id:
        raise ValueError("Not authorized to delete this chat session")
    
    return chat_crud.delete_chat_session(session, session_id)


async def send_message_stream(
    session: Session,
    user_id: int,
    chat_request: ChatRequest
) -> tuple[ChatSession, AsyncIterator[str]]:
    """Send a message and stream agent response.
    
    Returns:
        Tuple of (chat_session, async iterator of response chunks)
    """
    # Get or create chat session
    if chat_request.session_id:
        chat_session = chat_crud.get_chat_session_by_id(session, chat_request.session_id)
        if not chat_session:
            raise ValueError(f"Chat session {chat_request.session_id} not found")
        if chat_session.user_id != user_id:
            raise ValueError("Not authorized to access this chat session")
    else:
        chat_session = create_chat_session(session, user_id)
    
    # Save user message
    user_message = ChatMessageCreate(
        session_id=chat_session.id,
        role="user",
        content=chat_request.message,
    )
    chat_crud.create_chat_message(session, user_message)
    
    # Get chat history for context
    history = get_chat_history(session, chat_session.id)
    chat_history = []
    for msg in history[:-1]:  # Exclude the message we just added
        if msg.role == "user":
            chat_history.append((msg.content, ""))
        elif msg.role == "assistant" and chat_history:
            chat_history[-1] = (chat_history[-1][0], msg.content)
    
    # Stream agent response based on AGENT_TYPE setting
    session_id_str = str(chat_session.id)
    
    if settings.AGENT_TYPE == "langgraph":
        # Use LangGraph agent
        from backend.services.langgraph_agent import query_agent_stream as langgraph_query_agent_stream
        stream = langgraph_query_agent_stream(
            question=chat_request.message,
            chat_history=chat_history if chat_history else None,
            user_id=user_id,
            session_id=session_id_str,
            provider=chat_request.provider,
            model=chat_request.model,
        )
    else:
        # Use LangChain chain-based agent
        from backend.services.langchain_agent import query_agent_stream as langchain_query_agent_stream
        stream = langchain_query_agent_stream(
            question=chat_request.message,
            chat_history=chat_history if chat_history else None,
            user_id=user_id,
        )
    
    return chat_session, stream



