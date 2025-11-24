"""Chat routes."""
import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from backend.core.db import get_session
from backend.core.config import (
    get_enabled_providers,
    get_available_models_for_provider,
)
from backend.api.v1.auth import get_current_active_user
from backend.models.user import UserRead
from backend.models.chat import (
    ChatRequest,
    ChatResponse,
    ChatSessionRead,
    ChatMessageRead,
    ChatSessionCreate,
    ChatSessionUpdate,
)
from backend.services.chat_service import (
    create_chat_session,
    get_chat_history,
    send_message,
    send_message_stream,
    get_user_chat_sessions,
    update_chat_session as update_session_service,
    delete_chat_session as delete_session,
)
from backend.crud import chat_crud

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/providers")
async def get_available_providers(
    current_user: UserRead = Depends(get_current_active_user),
):
    """Get list of enabled providers with their available models.
    
    Returns:
        Dict mapping provider names to their available models
    """
    enabled_providers = get_enabled_providers()
    result = {}
    for provider in enabled_providers:
        models = get_available_models_for_provider(provider)
        if models:  # Only include providers with available models
            result[provider] = models
    return result


@router.post("/sessions", response_model=ChatSessionRead, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_create: ChatSessionCreate,
    current_user: UserRead = Depends(get_current_active_user),
    db: Session = Depends(get_session),
):
    """Create a new chat session."""
    chat_session = create_chat_session(db, current_user.id, session_create.title)
    return ChatSessionRead.model_validate(chat_session)


@router.get("/sessions", response_model=List[ChatSessionRead])
async def get_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: UserRead = Depends(get_current_active_user),
    db: Session = Depends(get_session),
):
    """Get user's chat sessions."""
    sessions = get_user_chat_sessions(db, current_user.id, skip, limit)
    return [ChatSessionRead.model_validate(session) for session in sessions]


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageRead])
async def get_messages(
    session_id: int,
    current_user: UserRead = Depends(get_current_active_user),
    db: Session = Depends(get_session),
):
    """Get messages for a chat session."""
    from backend.crud import chat_crud
    
    chat_session = chat_crud.get_chat_session_by_id(db, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    if chat_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    messages = get_chat_history(db, session_id)
    return [ChatMessageRead.model_validate(msg) for msg in messages]


@router.post("/", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    current_user: UserRead = Depends(get_current_active_user),
    db: Session = Depends(get_session),
):
    """Send a message and get agent response."""
    try:
        response = await send_message(db, current_user.id, chat_request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@router.patch("/sessions/{session_id}", response_model=ChatSessionRead)
async def update_session(
    session_id: int,
    session_update: ChatSessionUpdate,
    current_user: UserRead = Depends(get_current_active_user),
    db: Session = Depends(get_session),
):
    """Update a chat session."""
    try:
        updated_session = update_session_service(db, session_id, current_user.id, session_update)
        return ChatSessionRead.model_validate(updated_session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating session: {str(e)}")


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session_endpoint(
    session_id: int,
    current_user: UserRead = Depends(get_current_active_user),
    db: Session = Depends(get_session),
):
    """Delete a chat session."""
    try:
        success = delete_session(db, session_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Chat session not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stream")
async def chat_stream(
    chat_request: ChatRequest,
    current_user: UserRead = Depends(get_current_active_user),
    db: Session = Depends(get_session),
):
    """Send a message and get streaming agent response."""
    async def generate():
        try:
            chat_session, stream = await send_message_stream(db, current_user.id, chat_request)
            full_response = ""
            
            # Send session info first
            yield f"data: {json.dumps({'type': 'session', 'session_id': chat_session.id})}\n\n"
            
            # Stream response chunks
            async for chunk in stream:
                full_response += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            
            # Save complete assistant message
            from backend.models.chat import ChatMessageCreate
            assistant_message = ChatMessageCreate(
                session_id=chat_session.id,
                role="assistant",
                content=full_response,
            )
            chat_crud.create_chat_message(db, assistant_message)
            db.commit()
            
            # Send completion signal
            yield f"data: {json.dumps({'type': 'done', 'session_id': chat_session.id})}\n\n"
        except ValueError as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': f'Error processing chat: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )



