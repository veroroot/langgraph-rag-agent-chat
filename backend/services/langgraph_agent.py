"""LangGraph-based agent service."""
from typing import List, Optional, AsyncIterator
from backend.core.langgraph import LangGraphAgent
from backend.models.chat import Message
from backend.core.logging import logger


# Global instance (singleton pattern)
_langgraph_agent = None


def get_langgraph_agent() -> LangGraphAgent:
    """Get or create LangGraph agent instance."""
    global _langgraph_agent
    if _langgraph_agent is None:
        _langgraph_agent = LangGraphAgent()
    return _langgraph_agent


async def query_agent(
    question: str,
    chat_history: Optional[List[tuple]] = None,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> dict:
    """Query the agent with a question using LangGraph.
    
    Args:
        question: User's question
        chat_history: List of (question, answer) tuples
        user_id: User ID for filtering documents
        session_id: Optional session ID for conversation continuity
    
    Returns:
        Dict with answer and sources
    """
    try:
        agent = get_langgraph_agent()
        
        # Use session_id if provided, otherwise generate from user_id
        if session_id is None:
            session_id = f"user_{user_id}" if user_id else "default"
        
        # Convert chat history to Message format
        messages = []
        if chat_history:
            for q, a in chat_history:
                messages.append(Message(role="user", content=q))
                messages.append(Message(role="assistant", content=a))
        
        # Add current question
        messages.append(Message(role="user", content=question))
        
        # Get response from LangGraph agent
        response = await agent.get_response(
            messages=messages,
            session_id=session_id,
            user_id=user_id,
            provider=provider,
            model=model,
        )
        
        return response
    except Exception as e:
        logger.error(f"Error querying agent: {e}")
        raise


async def query_agent_stream(
    question: str,
    chat_history: Optional[List[tuple]] = None,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> AsyncIterator[str]:
    """Query the agent with a question and stream the response token by token using LangGraph.
    
    Args:
        question: User's question
        chat_history: List of (question, answer) tuples
        user_id: User ID for filtering documents
        session_id: Optional session ID for conversation continuity
    
    Yields:
        Chunks of the answer as strings (token by token)
    """
    try:
        agent = get_langgraph_agent()
        
        # Use session_id if provided, otherwise generate from user_id
        if session_id is None:
            session_id = f"user_{user_id}" if user_id else "default"
        
        # Convert chat history to Message format
        messages = []
        if chat_history:
            for q, a in chat_history:
                messages.append(Message(role="user", content=q))
                messages.append(Message(role="assistant", content=a))
        
        # Add current question
        messages.append(Message(role="user", content=question))
        
        # Stream response from LangGraph agent
        async for chunk in agent.get_stream_response(
            messages=messages,
            session_id=session_id,
            user_id=user_id,
            provider=provider,
            model=model,
        ):
            yield chunk
    except Exception as e:
        logger.error(f"Error streaming agent response: {e}", exc_info=True)
        raise

