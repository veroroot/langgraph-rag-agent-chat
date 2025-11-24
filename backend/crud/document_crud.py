"""Document CRUD operations."""
from sqlmodel import Session, select
from typing import Optional, List
from backend.models.document import Document, DocumentChunk, DocumentCreate, DocumentUpdate


def create_document(session: Session, document_create: DocumentCreate, owner_id: int, storage_path: str) -> Document:
    """Create a new document."""
    document = Document(
        **document_create.model_dump(),
        owner_id=owner_id,
        storage_path=storage_path,
    )
    session.add(document)
    session.commit()
    session.refresh(document)
    return document


def get_document_by_id(session: Session, document_id: int) -> Optional[Document]:
    """Get document by ID."""
    return session.get(Document, document_id)


def get_documents_by_owner(session: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[Document]:
    """Get documents by owner."""
    statement = select(Document).where(Document.owner_id == owner_id).offset(skip).limit(limit)
    return list(session.exec(statement).all())


def update_document(session: Session, document_id: int, document_update: DocumentUpdate) -> Optional[Document]:
    """Update document metadata."""
    document = session.get(Document, document_id)
    if not document:
        return None
    
    update_data = document_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)
    
    session.add(document)
    session.commit()
    session.refresh(document)
    return document


def delete_document(session: Session, document_id: int) -> bool:
    """Delete document and all associated chunks."""
    document = session.get(Document, document_id)
    if not document:
        return False
    
    # Delete all associated DocumentChunk records first
    # This is necessary because document_id has a NOT NULL constraint
    chunks_statement = select(DocumentChunk).where(DocumentChunk.document_id == document_id)
    chunks = session.exec(chunks_statement).all()
    for chunk in chunks:
        session.delete(chunk)
    
    # Now delete the document
    session.delete(document)
    session.commit()
    return True


def update_document_status(session: Session, document_id: int, status: str) -> Optional[Document]:
    """Update document processing status."""
    document = session.get(Document, document_id)
    if not document:
        return None
    
    document.status = status
    session.add(document)
    session.commit()
    session.refresh(document)
    return document



