"""Text extraction from various file formats."""
import os
from typing import Optional
from backend.core.logging import logger


def extract_text_from_file(file_path: str, mime_type: Optional[str] = None) -> str:
    """Extract text from file based on extension or mime type.
    
    Args:
        file_path: Path to the file
        mime_type: MIME type of the file (optional)
    
    Returns:
        Extracted text content
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext == ".txt" or mime_type == "text/plain":
            return extract_text_plain(file_path)
        elif file_ext == ".pdf" or mime_type == "application/pdf":
            return extract_text_pdf(file_path)
        elif file_ext in [".docx", ".doc"] or mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return extract_text_docx(file_path)
        elif file_ext == ".md" or mime_type == "text/markdown":
            return extract_text_plain(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_ext}")
            return ""
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")
        raise


def extract_text_plain(file_path: str) -> str:
    """Extract text from plain text file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_text_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    try:
        import PyPDF2
    except ImportError:
        logger.error("PyPDF2 not installed. Install with: pip install PyPDF2")
        raise ImportError("PyPDF2 is required for PDF extraction")
    
    text = ""
    with open(file_path, "rb") as f:
        pdf_reader = PyPDF2.PdfReader(f)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text


def extract_text_docx(file_path: str) -> str:
    """Extract text from DOCX file."""
    try:
        from docx import Document
    except ImportError:
        logger.error("python-docx not installed. Install with: pip install python-docx")
        raise ImportError("python-docx is required for DOCX extraction")
    
    doc = Document(file_path)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """Split text into chunks.
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk in characters
        chunk_overlap: Overlap between chunks in characters
    
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind(".")
            last_newline = chunk.rfind("\n")
            break_point = max(last_period, last_newline)
            if break_point > chunk_size // 2:  # Only break if it's not too early
                chunk = chunk[:break_point + 1]
                end = start + break_point + 1
        
        chunks.append(chunk.strip())
        start = end - chunk_overlap
    
    return chunks



