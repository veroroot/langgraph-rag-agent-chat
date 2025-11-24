"""Document upload routes."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlmodel import Session
from backend.core.db import get_session
from backend.api.v1.auth import get_current_active_user
from backend.models.user import UserRead
from backend.models.document import DocumentRead
from backend.services.document_service import upload_document

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: UserRead = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    """Upload a document."""
    try:
        document = await upload_document(session, file, current_user.id)
        return DocumentRead.model_validate(document)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")



