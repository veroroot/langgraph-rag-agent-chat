"""Document service for file upload and processing."""
import json
import uuid
from pathlib import Path
from sqlmodel import Session
from fastapi import UploadFile
from langchain_core.documents import Document as LangChainDocument
from backend.core.config import settings
from backend.core.logging import logger
from backend.crud import document_crud
from backend.models.document import Document, DocumentChunk, DocumentCreate, DocumentUpdate
from backend.utils.extractor import extract_text_from_file, chunk_text
from backend.utils.storage import storage
from backend.services.langchain_agent import get_vector_store


async def upload_document(
    session: Session,
    file: UploadFile,
    user_id: int
) -> Document:
    """Upload and process a document."""
    # Validate file
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise ValueError(f"File type {file_ext} not allowed")
    
    # Read file content
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise ValueError(f"File size exceeds maximum {settings.MAX_UPLOAD_SIZE} bytes")
    
    # Save file
    file_path = f"{file.filename}"
    storage_path = storage.save_file(content, file_path, user_id)
    
    # Create document record
    document_create = DocumentCreate(
        filename=file.filename,
        file_size=len(content),
        mime_type=file.content_type,
    )
    document = document_crud.create_document(session, document_create, user_id, storage_path)
    
    # Process document asynchronously (in background task)
    # For now, we'll process it synchronously
    try:
        process_document(session, document.id)
    except Exception as e:
        logger.error(f"Error processing document {document.id}: {e}")
        document_crud.update_document_status(session, document.id, "failed")
    
    return document


def process_document(session: Session, document_id: int):
    """Process document: extract text, chunk, and index."""
    document = document_crud.get_document_by_id(session, document_id)
    if not document:
        raise ValueError(f"Document {document_id} not found")
    
    # Update status to processing
    document_crud.update_document_status(session, document_id, "processing")
    
    try:
        # Extract text
        text = extract_text_from_file(document.storage_path, document.mime_type)
        if not text:
            raise ValueError("No text extracted from document")
        
        # Chunk text
        text_chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)
        
        if not text_chunks:
            raise ValueError("No chunks created from document")
        
        # Create LangChain Document objects with metadata
        # Generate unique IDs for each chunk to track them in vector store
        langchain_docs = []
        chunk_uuids = []
        for idx, chunk_content in enumerate(text_chunks):
            chunk_uuid = str(uuid.uuid4())
            chunk_uuids.append(chunk_uuid)
            
            metadata = {
                "document_id": document_id,
                "owner_id": document.owner_id,
                "filename": document.filename,
                "chunk_index": idx,
                "chunk_id": chunk_uuid,  # Store UUID in metadata for tracking
            }
            langchain_docs.append(
                LangChainDocument(
                    page_content=chunk_content,
                    metadata=metadata
                )
            )
        
        # Store in vector store
        vector_store = get_vector_store()
        # PGVector's add_documents returns a list of IDs (UUIDs)
        embedding_ids = vector_store.add_documents(langchain_docs)
        
        # If add_documents doesn't return IDs, use our generated UUIDs
        if not embedding_ids or len(embedding_ids) != len(chunk_uuids):
            embedding_ids = chunk_uuids
        
        # Create DocumentChunk records
        from datetime import datetime
        document_chunks = []
        for idx, (chunk_content, embedding_id) in enumerate(zip(text_chunks, embedding_ids)):
            chunk_meta = json.dumps({
                "filename": document.filename,
                "mime_type": document.mime_type,
            })
            
            document_chunk = DocumentChunk(
                document_id=document_id,
                chunk_text=chunk_content,
                chunk_index=idx,
                chunk_meta=chunk_meta,
                embedding_id=str(embedding_id) if embedding_id else None,
            )
            document_chunks.append(document_chunk)
        
        # Save chunks to database
        for chunk in document_chunks:
            session.add(chunk)
        
        # Update document status to completed
        document.status = "completed"
        document.processed_at = datetime.utcnow()
        session.add(document)
        session.commit()
        
        logger.info(
            f"Processed document {document_id}: {len(text_chunks)} chunks indexed and stored"
        )
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        document_crud.update_document_status(session, document_id, "failed")
        session.rollback()
        raise


def get_user_documents(session: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[Document]:
    """Get documents for a user."""
    return document_crud.get_documents_by_owner(session, user_id, skip, limit)


def update_document_metadata(
    session: Session,
    document_id: int,
    document_update: DocumentUpdate,
    user_id: int
) -> Document:
    """Update document metadata."""
    document = document_crud.get_document_by_id(session, document_id)
    if not document:
        raise ValueError(f"Document {document_id} not found")
    
    if document.owner_id != user_id:
        raise ValueError("Not authorized to update this document")
    
    updated = document_crud.update_document(session, document_id, document_update)
    if not updated:
        raise ValueError(f"Failed to update document {document_id}")
    
    return updated


def delete_document(session: Session, document_id: int, user_id: int) -> bool:
    """Delete document."""
    document = document_crud.get_document_by_id(session, document_id)
    if not document:
        raise ValueError(f"Document {document_id} not found")
    
    if document.owner_id != user_id:
        raise ValueError("Not authorized to delete this document")
    
    try:
        # Delete from vector store using metadata filter
        vector_store = get_vector_store()
        try:
            # PGVector supports delete by metadata filter
            # Delete all chunks associated with this document
            if hasattr(vector_store, 'delete'):
                # Try to delete using metadata filter
                vector_store.delete(filter={"document_id": document_id})
            else:
                # If delete method doesn't exist, log a warning
                logger.warning(
                    f"Vector store does not support delete method. "
                    f"Chunks for document {document_id} may remain in vector store."
                )
        except Exception as e:
            logger.warning(f"Error deleting from vector store: {e}. Continuing with document deletion.")
        
        # Delete file from storage
        storage.delete_file(document.storage_path)
        
        # Delete document record (this will cascade delete DocumentChunk records)
        return document_crud.delete_document(session, document_id)
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise



