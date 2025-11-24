"""Graph state definition for LangGraph agent."""
from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from operator import add


class GraphState(TypedDict):
    """State for the LangGraph agent.
    
    Attributes:
        messages: List of messages in the conversation
        user_id: User ID for filtering documents
        retrieved_documents: Retrieved documents from RAG
        provider: Optional provider name to use for this conversation
        model: Optional model name to use for this conversation
    """
    messages: Annotated[Sequence[BaseMessage], add]
    user_id: int | None
    retrieved_documents: list[dict] | None
    provider: str | None
    model: str | None

