"""Document management routes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session
from backend.core.db import get_session
from backend.api.v1.auth import get_current_active_user
from backend.models.user import UserRead
from backend.models.document import DocumentRead, DocumentUpdate
from backend.services.document_service import (
    get_user_documents,
    update_document_metadata,
    delete_document,
)

router = APIRouter(prefix="/docs", tags=["documents"])


@router.get("/", response_model=List[DocumentRead])
async def get_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: UserRead = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Get user's documents."""
    documents = get_user_documents(session, current_user.id, skip, limit)
    return [DocumentRead.model_validate(doc) for doc in documents]


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: int,
    current_user: UserRead = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Get a specific document."""
    from backend.crud import document_crud
    
    document = document_crud.get_document_by_id(session, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return DocumentRead.model_validate(document)


@router.patch("/{document_id}", response_model=DocumentRead)
async def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    current_user: UserRead = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Update document metadata."""
    try:
        document = update_document_metadata(session, document_id, document_update, current_user.id)
        return DocumentRead.model_validate(document)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_endpoint(
    document_id: int,
    current_user: UserRead = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Delete a document."""
    try:
        success = delete_document(session, document_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))



