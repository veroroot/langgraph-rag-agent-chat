"""Document model."""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class DocumentBase(SQLModel):
    """Base document schema."""
    filename: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    status: str = "pending"  # pending, processing, completed, failed


class Document(DocumentBase, table=True):
    """Document database model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id")
    storage_path: str
    uploaded_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    chunks: List["DocumentChunk"] = Relationship(back_populates="document")


class DocumentChunk(SQLModel, table=True):
    """Document chunk model for vector storage."""
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id")
    chunk_text: str
    chunk_index: int
    chunk_meta: Optional[str] = None  # JSON string for metadata
    embedding_id: Optional[str] = None  # Reference to embedding in vector store
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    document: Optional[Document] = Relationship(back_populates="chunks")


class DocumentCreate(SQLModel):
    """Schema for creating a document."""
    filename: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


class DocumentRead(DocumentBase):
    """Schema for reading document data."""
    id: int
    owner_id: int
    storage_path: str
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DocumentUpdate(SQLModel):
    """Schema for updating document metadata."""
    filename: Optional[str] = None



