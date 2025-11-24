"""Tools for LangGraph agent."""
from typing import Optional
from langchain_core.tools import tool
from langchain_core.documents import Document
from backend.services.langchain_agent import get_retriever
from backend.core.logging import logger


@tool
async def retrieve_documents(query: str, user_id: Optional[int] = None, k: int = 5) -> list[dict]:
    """Retrieve relevant documents from the vector store based on the query.
    
    This tool searches the vector store for documents that are relevant to the user's query.
    It filters documents by user_id if provided to ensure users only see their own documents.
    
    Args:
        query: The search query string
        user_id: Optional user ID to filter documents by owner
        k: Number of documents to retrieve (default: 5)
    
    Returns:
        List of dictionaries containing document content and metadata
    """
    try:
        retriever = get_retriever(k=k, user_id=user_id)
        documents = await retriever.ainvoke(query)
        
        results = []
        for doc in documents:
            if isinstance(doc, Document):
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                })
            else:
                # Handle other document types
                results.append({
                    "content": str(doc),
                    "metadata": {},
                })
        
        query_preview = query[:100] if len(query) > 100 else query
        logger.info(f"Retrieved {len(results)} documents for user_id={user_id}, query='{query_preview}...'")
        
        return results
    except Exception as e:
        logger.error(f"Error retrieving documents for user_id={user_id}, query='{query[:50]}...': {str(e)}")
        return []


# Export tools list
tools = [retrieve_documents]

