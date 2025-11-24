"""LangChain chain-based agent service."""
from typing import List, Optional, AsyncIterator
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import PGVector, Milvus
from langchain_core.documents import Document
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.chains.conversational_retrieval.base import ConversationalRetrievalChain
from backend.core.config import settings
from backend.core.logging import logger


# Global instances (singleton pattern)
_llm = None
_embeddings = None
_vector_store = None


def get_llm():
    """Get or create LLM instance."""
    global _llm
    if _llm is None:
        if settings.LLM_PROVIDER == "openai":
            _llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                api_key=settings.OPENAI_API_KEY,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")
    return _llm


def get_embedding_model():
    """Get or create embedding model instance."""
    global _embeddings
    if _embeddings is None:
        if settings.EMBEDDING_PROVIDER == "openai":
            _embeddings = OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                api_key=settings.OPENAI_API_KEY,
            )
        else:
            raise ValueError(f"Unsupported embedding provider: {settings.EMBEDDING_PROVIDER}")
    return _embeddings


def get_vector_store():
    """Get or create vector store instance."""
    global _vector_store
    if _vector_store is None:
        embeddings = get_embedding_model()
        if settings.VECTOR_STORE_TYPE == "pgvector":
            _vector_store = PGVector(
                connection_string=settings.DATABASE_URL,
                embedding_function=embeddings,
                collection_name=settings.VECTOR_COLLECTION_NAME,
            )
            logger.info(
                "Connected to pgvector collection '%s'",
                settings.VECTOR_COLLECTION_NAME,
            )
        elif settings.VECTOR_STORE_TYPE == "milvus":
            connection_args = {
                "host": settings.MILVUS_HOST,
                "port": str(settings.MILVUS_PORT),
                "db_name": settings.MILVUS_DB_NAME,
            }
            if settings.MILVUS_USER:
                connection_args["user"] = settings.MILVUS_USER
            if settings.MILVUS_PASSWORD:
                connection_args["password"] = settings.MILVUS_PASSWORD
            if settings.MILVUS_SECURE:
                connection_args["secure"] = True

            _vector_store = Milvus(
                embedding_function=embeddings,
                collection_name=settings.VECTOR_COLLECTION_NAME,
                connection_args=connection_args,
                consistency_level=settings.MILVUS_CONSISTENCY_LEVEL,
            )
            logger.info("Connected to Milvus collection '%s'", settings.VECTOR_COLLECTION_NAME)
        else:
            raise ValueError(
                f"Unsupported vector store type: {settings.VECTOR_STORE_TYPE}. "
                f"Supported types: pgvector, milvus"
            )
    return _vector_store


def get_retriever(k: int = 5, user_id: Optional[int] = None):
    """Get retriever from vector store.
    
    Args:
        k: Number of documents to retrieve
        user_id: User ID for filtering documents by owner_id
    """
    vector_store = get_vector_store()
    search_kwargs = {"k": k}
    
    # Add metadata filter if user_id is provided
    if user_id is not None:
        if settings.VECTOR_STORE_TYPE == "pgvector":
            # PGVector uses dictionary filter
            search_kwargs["filter"] = {"owner_id": user_id}
        elif settings.VECTOR_STORE_TYPE == "milvus":
            # Milvus uses expression string
            search_kwargs["expr"] = f'owner_id == {user_id}'
    
    return vector_store.as_retriever(search_kwargs=search_kwargs)


def get_qa_chain(user_id: Optional[int] = None):
    """Get conversational retrieval chain.
    
    Args:
        user_id: User ID for filtering documents by owner_id
    """
    llm = get_llm()
    retriever = get_retriever(user_id=user_id)
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",  # Explicitly set output key since chain returns multiple keys
    )
    
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
        # Don't rephrase question - use original question for final answer
        # This reduces intermediate processing
        rephrase_question=False,
        return_generated_question=False,
    )
    return chain


def query_agent(
    question: str,
    chat_history: Optional[List[tuple]] = None,
    user_id: Optional[int] = None
) -> dict:
    """Query the agent with a question using ConversationalRetrievalChain.
    
    Args:
        question: User's question
        chat_history: List of (question, answer) tuples
        user_id: User ID for filtering documents
    
    Returns:
        Dict with answer and sources
    """
    try:
        chain = get_qa_chain(user_id=user_id)
        
        # If chat history exists, add it to memory
        if chat_history:
            for q, a in chat_history:
                chain.memory.chat_memory.add_user_message(q)
                chain.memory.chat_memory.add_ai_message(a)
        
        # Run chain
        result = chain.invoke({"question": question})
        
        # Extract sources
        sources = []
        if "source_documents" in result:
            for doc in result["source_documents"]:
                sources.append({
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "metadata": doc.metadata,
                })
        
        return {
            "answer": result.get("answer", ""),
            "sources": sources,
        }
    except Exception as e:
        logger.error(f"Error querying agent: {e}")
        raise


def add_documents_to_vector_store(documents: List[Document], user_id: Optional[int] = None):
    """Add documents to vector store.
    
    Args:
        documents: List of Document objects
        user_id: User ID for metadata filtering
    """
    vector_store = get_vector_store()
    
    # Add user_id to metadata if provided
    if user_id:
        for doc in documents:
            if doc.metadata is None:
                doc.metadata = {}
            doc.metadata["user_id"] = user_id
    
    vector_store.add_documents(documents)


def _extract_content_from_chunk(chunk, data: dict) -> Optional[str]:
    """Extract text content from a chunk object."""
    if chunk:
        # Handle AIMessageChunk - most common case
        if hasattr(chunk, 'content'):
            chunk_content = chunk.content
            if isinstance(chunk_content, str):
                return chunk_content
            elif isinstance(chunk_content, list):
                # Extract text from content blocks
                text_parts = [block.get('text') if isinstance(block, dict) else block 
                             for block in chunk_content if block]
                return ''.join(text_parts) if text_parts else None
        # Fallback to text attribute
        if hasattr(chunk, 'text'):
            return chunk.text
        # Handle dict chunks
        if isinstance(chunk, dict):
            return chunk.get('content') or chunk.get('text') or chunk.get('delta', {}).get('content')
        # Handle string chunks
        if isinstance(chunk, str):
            return chunk
    
    # Try to get from data directly
    if "content" in data:
        return data["content"]
    if "text" in data:
        return data["text"]
    if "delta" in data and isinstance(data["delta"], dict):
        return data["delta"].get('content') or data["delta"].get('text')
    
    return None


def _is_question_generation(event_name: str, path_str: str) -> bool:
    """Check if event is from question generation step."""
    return any(keyword in event_name or keyword in path_str 
               for keyword in ["question_generator", "condense_question", "condense"])


def _is_final_answer(event_name: str, path_str: str, question_gen_completed: bool) -> bool:
    """Check if event is from final answer generation."""
    # Direct indicators
    if any(keyword in event_name or keyword in path_str 
           for keyword in ["combine_docs", "stuff_documents", "qa_chain"]):
        return True
    # If question generation completed or doesn't exist, accept non-retriever LLM events
    if question_gen_completed and "retriever" not in event_name and "retriever" not in path_str:
        return True
    return False


async def query_agent_stream(
    question: str,
    chat_history: Optional[List[tuple]] = None,
    user_id: Optional[int] = None
) -> AsyncIterator[str]:
    """Query the agent with a question and stream the response token by token.
    
    Args:
        question: User's question
        chat_history: List of (question, answer) tuples
        user_id: User ID for filtering documents
    
    Yields:
        Chunks of the answer as strings (token by token)
    """
    try:
        chain = get_qa_chain(user_id=user_id)
        
        # Add chat history to memory
        if chat_history:
            for q, a in chat_history:
                chain.memory.chat_memory.add_user_message(q)
                chain.memory.chat_memory.add_ai_message(a)
        
        question_gen_completed = False
        streamed_any = False
        # Stream events and filter for final answer only
        async for event in chain.astream_events({"question": question}, version="v2"):
            event_type = event.get("event")
            event_name = event.get("name", "").lower()
            path_str = "/".join(str(p) for p in event.get("path", [])).lower()
            
            # Track question generation completion
            if "question_generator" in event_name or "question_generator" in path_str:
                if event_type == "on_chain_end":
                    question_gen_completed = True
                continue
            
            # Only process LLM streaming events
            if event_type not in ["on_llm_stream", "on_chat_model_stream", "on_chat_model_chunk", "on_llm_new_token"]:
                continue
            
            # Skip question generation events
            if _is_question_generation(event_name, path_str):
                continue
            
            # Only process final answer events
            if not _is_final_answer(event_name, path_str, question_gen_completed):
                continue
            
            # Extract and yield content
            data = event.get("data", {})
            
            if event_type == "on_llm_new_token":
                token = data.get("token")
                if token:
                    streamed_any = True
                    yield token
            else:
                chunk = data.get("chunk")
                content = _extract_content_from_chunk(chunk, data)
                
                if content:
                    content = str(content).strip()
                    if content:
                        streamed_any = True
                        yield content
        
        # Fallback if no tokens were streamed
        if not streamed_any:
            logger.warning("astream_events didn't yield tokens, trying astream fallback")
            # Try astream - it may yield chunks if LLM supports streaming
            async for chunk in chain.astream({"question": question}):
                # Check if chunk is a dict with answer key (typical case)
                if isinstance(chunk, dict) and "answer" in chunk:
                    answer = chunk["answer"]
                    if answer:
                        # If answer is a string, it's likely the complete answer
                        # Split into characters for streaming effect
                        for char in answer:
                            yield char
                        break
                # Check if chunk is already a string/token (streaming case)
                elif isinstance(chunk, str):
                    if chunk:
                        streamed_any = True
                        yield chunk
                # Check if chunk has content attribute (AIMessageChunk, etc.)
                elif hasattr(chunk, 'content'):
                    content = chunk.content
                    if content:
                        streamed_any = True
                        yield str(content)
    except Exception as e:
        logger.error(f"Error streaming agent response: {e}", exc_info=True)
        # Final fallback
        try:
            chain = get_qa_chain(user_id=user_id)
            if chat_history:
                for q, a in chat_history:
                    chain.memory.chat_memory.add_user_message(q)
                    chain.memory.chat_memory.add_ai_message(a)
            
            result = await chain.ainvoke({"question": question})
            answer = result.get("answer", "")
            if answer:
                for char in answer:
                    yield char
        except Exception as fallback_error:
            logger.error(f"Fallback streaming also failed: {fallback_error}", exc_info=True)
            raise



