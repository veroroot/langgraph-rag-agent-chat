"""Utility functions for LangGraph agent."""
from typing import List
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)
from backend.core.prompts.system import SYSTEM_PROMPT, AGENT_PROMPT
from backend.core.logging import logger


def prepare_messages(
    messages: List[BaseMessage],
    llm,
    system_prompt: str = None,
    retrieved_docs: List[dict] = None,  # Deprecated: system_prompt에 이미 포함됨
) -> List[BaseMessage]:
    """Prepare messages for LLM with system prompt and context.
    
    Args:
        messages: List of conversation messages
        llm: LLM instance (for checking if it needs system message)
        system_prompt: Optional system prompt (should already include retrieved_docs context)
        retrieved_docs: Deprecated - system_prompt에 이미 포함되어 있으므로 사용하지 않음
    
    Returns:
        List of messages with system prompt prepended
    """
    prepared = []
    
    # Add system prompt if provided
    # Note: system_prompt should already include retrieved_docs context from load_system_prompt()
    if system_prompt:
        # Check if LLM supports system messages
        if hasattr(llm, "model_name") or hasattr(llm, "model"):
            prepared.append(SystemMessage(content=system_prompt))
        else:
            # For LLMs that don't support system messages, prepend to first human message
            if messages and isinstance(messages[0], HumanMessage):
                messages[0].content = f"{system_prompt}\n\n{messages[0].content}"
    
    # Note: retrieved_docs는 load_system_prompt()에서 이미 system_prompt에 포함되므로
    # 여기서는 중복으로 추가하지 않음
    
    prepared.extend(messages)
    return prepared


def dump_messages(messages: List[BaseMessage]) -> List[BaseMessage]:
    """Convert messages to LangChain format.
    
    Args:
        messages: List of messages (can be dict or BaseMessage)
    
    Returns:
        List of BaseMessage objects
    """
    result = []
    for msg in messages:
        if isinstance(msg, BaseMessage):
            result.append(msg)
        elif isinstance(msg, dict):
            # Convert dict to message
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                result.append(HumanMessage(content=content))
            elif role == "assistant":
                result.append(AIMessage(content=content))
            elif role == "system":
                result.append(SystemMessage(content=content))
        else:
            logger.warning(f"Unknown message type: {type(msg)}")
    return result


def process_llm_response(response_message: BaseMessage) -> BaseMessage:
    """Process LLM response to handle structured content blocks.
    
    Args:
        response_message: LLM response message
    
    Returns:
        Processed message
    """
    # Handle structured content if needed
    if hasattr(response_message, "content"):
        if isinstance(response_message.content, list):
            # Extract text from content blocks
            text_parts = []
            for block in response_message.content:
                if isinstance(block, dict):
                    if "text" in block:
                        text_parts.append(block["text"])
                    elif "type" in block and block["type"] == "text":
                        text_parts.append(block.get("text", ""))
                elif isinstance(block, str):
                    text_parts.append(block)
            
            if text_parts:
                # Create new message with text content
                response_message.content = "".join(text_parts)
    
    return response_message


def load_system_prompt(retrieved_docs: List[dict] = None) -> str:
    """Load system prompt with optional RAG context.
    
    Args:
        retrieved_docs: Optional retrieved documents
    
    Returns:
        System prompt string
    """
    if retrieved_docs:
        context = "\n\n".join([
            f"Document {i+1}:\n{doc.get('content', '')[:500]}..."
            for i, doc in enumerate(retrieved_docs[:5])
        ])
        return SYSTEM_PROMPT.format(context=context, question="{question}")
    else:
        return AGENT_PROMPT

