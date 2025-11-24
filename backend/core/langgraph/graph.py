"""LangGraph agent implementation with RAG support."""
from typing import AsyncGenerator, Optional, List
from urllib.parse import quote_plus

from asgiref.sync import sync_to_async
from langchain_core.messages import (
    ToolMessage,
    HumanMessage,
    AIMessage,
    convert_to_openai_messages,
)
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import (
    END,
    StateGraph,
)
from langgraph.graph.state import (
    Command,
    CompiledStateGraph,
)
from langgraph.types import (
    RunnableConfig,
    StateSnapshot,
)
from psycopg_pool import AsyncConnectionPool

from backend.core.config import (
    settings,
    get_provider_api_key,
    is_provider_enabled,
    get_available_models_for_provider,
)
from backend.core.langgraph.state import GraphState
from backend.core.langgraph.tools import tools
from backend.core.langgraph.utils import (
    prepare_messages,
    process_llm_response,
    load_system_prompt,
)
from backend.core.logging import logger
from backend.models.chat import Message


class LangGraphAgent:
    """Manages the LangGraph Agent/workflow with RAG support.

    This class handles the creation and management of the LangGraph workflow,
    including LLM interactions, database connections, and RAG retrieval.
    """

    def __init__(self):
        """Initialize the LangGraph Agent with necessary components."""
        # Initialize LLM with tools bound
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            api_key=settings.OPENAI_API_KEY,
        )
        self.llm_with_tools = self.llm.bind_tools(tools)
        self.tools_by_name = {tool.name: tool for tool in tools}
        self._connection_pool: Optional[AsyncConnectionPool] = None
        self._graph: Optional[CompiledStateGraph] = None
        
        logger.info(
            f"LangGraph agent initialized - Provider: {settings.LLM_PROVIDER}, "
            f"Model: {settings.LLM_MODEL}, Temperature: {settings.LLM_TEMPERATURE}"
        )

    async def _get_connection_pool(self) -> AsyncConnectionPool:
        """Get a PostgreSQL connection pool for checkpointing.

        Returns:
            AsyncConnectionPool: A connection pool for PostgreSQL database.
        """
        if self._connection_pool is None:
            try:
                max_size = settings.POSTGRES_POOL_SIZE

                # Use DATABASE_URL if available, otherwise construct from individual settings
                # This ensures consistency with the main database connection
                if settings.DATABASE_URL:
                    connection_url = settings.DATABASE_URL
                else:
                    connection_url = (
                        "postgresql://"
                        f"{quote_plus(settings.POSTGRES_USER)}:{quote_plus(settings.POSTGRES_PASSWORD)}"
                        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
                    )

                self._connection_pool = AsyncConnectionPool(
                    connection_url,
                    open=False,
                    max_size=max_size,
                    kwargs={
                        "autocommit": True,
                        "connect_timeout": 5,
                        "prepare_threshold": None,
                    },
                )
                await self._connection_pool.open()
                logger.info(f"Connection pool created with max_size={max_size} using DATABASE_URL")
            except Exception as e:
                logger.error(f"Connection pool creation failed: {str(e)}")
                raise e
        return self._connection_pool

    async def _retrieve_documents(self, state: GraphState, config: RunnableConfig) -> Command:
        """Retrieve relevant documents using RAG tool.
        
        Args:
            state: Current graph state
            config: Runnable config
            
        Returns:
            Command with retrieved documents
        """
        user_id = state.get("user_id")
        last_message = state["messages"][-1]
        
        # Extract query from last human message
        query = last_message.content if hasattr(last_message, "content") else str(last_message)
        
        try:
            # Use retrieve_documents tool
            retrieve_tool = self.tools_by_name["retrieve_documents"]
            retrieved_docs = await retrieve_tool.ainvoke({
                "query": query,
                "user_id": user_id,
                "k": 5,
            })
            
            session_id = config.get("configurable", {}).get("thread_id", "unknown")
            logger.info(f"Retrieved {len(retrieved_docs)} documents for session {session_id}")
            
            return Command(update={"retrieved_documents": retrieved_docs})
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return Command(update={"retrieved_documents": []})

    def _get_llm_for_provider_and_model(
        self, 
        provider: Optional[str] = None, 
        model_name: Optional[str] = None
    ) -> BaseChatModel:
        """Get LLM instance for a specific provider and model.
        
        Args:
            provider: Provider name (e.g., 'openai', 'anthropic'), defaults to settings.LLM_PROVIDER
            model_name: Model name to use, defaults to settings.LLM_MODEL
            
        Returns:
            BaseChatModel instance configured for the specified provider and model
        """
        # Use default provider if not specified
        if provider is None:
            provider = settings.LLM_PROVIDER
        
        provider = provider.lower()
        
        # Check if provider is enabled
        if not is_provider_enabled(provider):
            logger.warning(f"Provider {provider} is not enabled, using default {settings.LLM_PROVIDER}")
            provider = settings.LLM_PROVIDER
        
        # Get API key for provider
        api_key = get_provider_api_key(provider)
        if not api_key:
            raise ValueError(f"API key not configured for provider: {provider}")
        
        # Use default model if not specified
        if model_name is None:
            model_name = settings.LLM_MODEL
        
        # Validate model name for provider
        available_models = get_available_models_for_provider(provider)
        if available_models and model_name not in available_models:
            logger.warning(
                f"Model {model_name} not in available models for {provider}, "
                f"using first available model: {available_models[0] if available_models else settings.LLM_MODEL}"
            )
            model_name = available_models[0] if available_models else settings.LLM_MODEL
        
        # Create LLM instance based on provider
        if provider == "openai":
            return ChatOpenAI(
                model=model_name,
                temperature=settings.LLM_TEMPERATURE,
                api_key=api_key,
            )
        elif provider == "anthropic":
            # Try to import ChatAnthropic
            try:
                from langchain_anthropic import ChatAnthropic  # type: ignore
                return ChatAnthropic(
                    model=model_name,
                    temperature=settings.LLM_TEMPERATURE,
                    api_key=api_key,
                )
            except ImportError:
                # Fallback to langchain_community if langchain_anthropic is not available
                try:
                    from langchain_community.chat_models import ChatAnthropic
                    return ChatAnthropic(
                        model=model_name,
                        temperature=settings.LLM_TEMPERATURE,
                        anthropic_api_key=api_key,
                    )
                except ImportError:
                    raise ValueError(
                        "Anthropic provider requires langchain-anthropic or langchain-community. "
                        "Install with: pip install langchain-anthropic"
                    )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def _chat(self, state: GraphState, config: RunnableConfig) -> Command:
        """Process the chat state and generate a response.

        Args:
            state: The current state of the conversation
            config: Runnable config

        Returns:
            Command: Command object with updated state and next node to execute.
        """
        # Get provider and model from state, or use defaults
        provider = state.get("provider") or settings.LLM_PROVIDER
        model_name = state.get("model") or settings.LLM_MODEL
        
        # Get LLM instance for the specified provider and model
        llm = self._get_llm_for_provider_and_model(provider, model_name)
        llm_with_tools = llm.bind_tools(tools)
        
        # Get retrieved documents for context
        retrieved_docs = state.get("retrieved_documents", [])
        
        # Load system prompt with RAG context
        system_prompt = load_system_prompt(retrieved_docs=retrieved_docs)
        
        # Prepare messages with system prompt
        # Note: system_prompt already includes retrieved_docs context from load_system_prompt()
        messages = prepare_messages(
            state["messages"],
            llm,
            system_prompt=system_prompt,
        )

        try:
            # Call LLM with tools
            response_message = await llm_with_tools.ainvoke(messages)
            
            # Process response to handle structured content blocks
            response_message = process_llm_response(response_message)

            session_id = config.get("configurable", {}).get("thread_id", "unknown")
            logger.info(f"LLM response generated for session {session_id} using provider {provider}, model {model_name}")

            # Determine next node based on whether there are tool calls
            if response_message.tool_calls:
                goto = "tool_call"
            else:
                goto = END

            return Command(update={"messages": [response_message]}, goto=goto)
        except Exception as e:
            session_id = config.get("configurable", {}).get("thread_id", "unknown")
            logger.error(f"LLM call failed for session {session_id}: {str(e)}")
            raise Exception(f"Failed to get LLM response: {str(e)}")

    async def _tool_call(self, state: GraphState, config: RunnableConfig) -> Command:
        """Process tool calls from the last message.

        Args:
            state: The current agent state containing messages and tool calls.
            config: Runnable config

        Returns:
            Command: Command object with updated messages and routing back to chat.
        """
        outputs = []
        last_message = state["messages"][-1]
        
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Add user_id to tool args if available
            if "user_id" not in tool_args and state.get("user_id"):
                tool_args["user_id"] = state["user_id"]
            
            try:
                tool_result = await self.tools_by_name[tool_name].ainvoke(tool_args)
                outputs.append(
                    ToolMessage(
                        content=str(tool_result),
                        name=tool_name,
                        tool_call_id=tool_call["id"],
                    )
                )
            except Exception as e:
                logger.error(f"Tool call failed for {tool_name}: {str(e)}")
                outputs.append(
                    ToolMessage(
                        content=f"Error calling tool {tool_name}: {str(e)}",
                        name=tool_name,
                        tool_call_id=tool_call["id"],
                    )
                )
        
        return Command(update={"messages": outputs}, goto="chat")

    async def create_graph(self) -> CompiledStateGraph:
        """Create and configure the LangGraph workflow.

        Returns:
            CompiledStateGraph: The configured LangGraph instance
        """
        if self._graph is None:
            try:
                graph_builder = StateGraph(GraphState)
                
                # Add nodes
                graph_builder.add_node("retrieve", self._retrieve_documents)
                graph_builder.add_node("chat", self._chat, ends=["tool_call", END])
                graph_builder.add_node("tool_call", self._tool_call, ends=["chat"])
                
                # Set entry point
                graph_builder.set_entry_point("retrieve")
                
                # Add edges
                graph_builder.add_edge("retrieve", "chat")
                
                # Get connection pool for checkpointing
                connection_pool = await self._get_connection_pool()
                checkpointer = AsyncPostgresSaver(connection_pool)
                await checkpointer.setup()

                self._graph = graph_builder.compile(
                    checkpointer=checkpointer,
                    name=f"{settings.PROJECT_NAME} Agent",
                )

                logger.info(f"Graph created: {settings.PROJECT_NAME} Agent (with checkpointer)")
            except Exception as e:
                logger.error(f"Graph creation failed: {str(e)}")
                raise e

        return self._graph

    async def get_response(
        self,
        messages: List[Message],
        session_id: str,
        user_id: Optional[int] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> dict:
        """Get a response from the LLM.

        Args:
            messages: The messages to send to the LLM
            session_id: The session ID for checkpointing
            user_id: Optional user ID for filtering documents

        Returns:
            dict: Response with answer and sources
        """
        if self._graph is None:
            self._graph = await self.create_graph()
        
        # Convert messages to LangChain format
        langchain_messages = []
        for msg in messages:
            if msg.role == "user":
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                langchain_messages.append(AIMessage(content=msg.content))
        
        config = {
            "configurable": {"thread_id": session_id},
            "metadata": {
                "user_id": user_id,
                "session_id": session_id,
            },
        }
        
        # Use provided provider/model or defaults
        provider_name = provider or settings.LLM_PROVIDER
        model_name = model or settings.LLM_MODEL
        
        try:
            response = await self._graph.ainvoke(
                input={
                    "messages": langchain_messages,
                    "user_id": user_id,
                    "retrieved_documents": None,
                    "provider": provider_name,
                    "model": model_name,
                },
                config=config,
            )
            
            # Extract sources from retrieved documents
            sources = []
            retrieved_docs = response.get("retrieved_documents", [])
            if retrieved_docs:
                for doc in retrieved_docs:
                    sources.append({
                        "content": doc.get("content", "")[:200] + "..." if len(doc.get("content", "")) > 200 else doc.get("content", ""),
                        "metadata": doc.get("metadata", {}),
                    })
            
            # Get last assistant message
            assistant_messages = [
                msg for msg in response["messages"]
                if isinstance(msg, AIMessage) and not msg.tool_calls
            ]
            answer = assistant_messages[-1].content if assistant_messages else ""
            
            return {
                "answer": answer,
                "sources": sources,
            }
        except Exception as e:
            logger.error(f"Error getting response: {str(e)}")
            raise

    async def get_stream_response(
        self,
        messages: List[Message],
        session_id: str,
        user_id: Optional[int] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Get a stream response from the LLM.

        Args:
            messages: The messages to send to the LLM
            session_id: The session ID for the conversation
            user_id: Optional user ID for filtering documents

        Yields:
            str: Tokens of the LLM response
        """
        if self._graph is None:
            self._graph = await self.create_graph()
        
        # Convert messages to LangChain format
        langchain_messages = []
        for msg in messages:
            if msg.role == "user":
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                langchain_messages.append(AIMessage(content=msg.content))
        
        config = {
            "configurable": {"thread_id": session_id},
            "metadata": {
                "user_id": user_id,
                "session_id": session_id,
            },
        }

        # Use provided provider/model or defaults
        provider_name = provider or settings.LLM_PROVIDER
        model_name = model or settings.LLM_MODEL

        try:
            # Use astream with stream_mode="messages" - returns (message, metadata) tuples
            # Reference: https://github.com/wassim249/fastapi-langgraph-agent-production-ready-template
            async for token, _ in self._graph.astream(
                {
                    "messages": langchain_messages,
                    "user_id": user_id,
                    "retrieved_documents": None,
                    "provider": provider_name,
                    "model": model_name,
                },
                config,
                stream_mode="messages",
            ):
                try:
                    # Extract content from the message token
                    if hasattr(token, "content"):
                        content = token.content
                        if isinstance(content, str) and content:
                            # Only yield if it's an AIMessage without tool calls
                            if isinstance(token, AIMessage) and not token.tool_calls:
                                yield content
                        elif isinstance(content, list):
                            # Handle structured content blocks
                            for block in content:
                                if isinstance(block, dict) and "text" in block:
                                    yield block["text"]
                                elif isinstance(block, str):
                                    yield block
                except Exception as token_error:
                    logger.error(f"Error processing token for session {session_id}: {str(token_error)}")
                    # Continue with next token even if current one fails
                    continue
        except Exception as stream_error:
            logger.error(f"Error in stream processing for session {session_id}: {str(stream_error)}")
            raise stream_error

    async def get_chat_history(self, session_id: str) -> List[Message]:
        """Get the chat history for a given thread ID.

        Args:
            session_id: The session ID for the conversation

        Returns:
            List[Message]: The chat history
        """
        if self._graph is None:
            self._graph = await self.create_graph()

        state: StateSnapshot = await sync_to_async(self._graph.get_state)(
            config={"configurable": {"thread_id": session_id}}
        )
        
        if not state.values:
            return []
        
        messages = state.values.get("messages", [])
        openai_style_messages = convert_to_openai_messages(messages)
        
        # Keep just assistant and user messages
        return [
            Message(role=message["role"], content=str(message["content"]))
            for message in openai_style_messages
            if message["role"] in ["assistant", "user"] and message["content"]
        ]

    async def clear_chat_history(self, session_id: str) -> None:
        """Clear all chat history for a given thread ID.

        Args:
            session_id: The ID of the session to clear history for

        Raises:
            Exception: If there's an error clearing the chat history
        """
        try:
            conn_pool = await self._get_connection_pool()

            async with conn_pool.connection() as conn:
                async with conn.cursor() as cur:
                    for table in settings.CHECKPOINT_TABLES:
                        try:
                            # Note: autocommit=True is set in connection pool, so no explicit commit needed
                            await cur.execute(f"DELETE FROM {table} WHERE thread_id = %s", (session_id,))
                            logger.info(f"Cleared {table} for session {session_id}")
                        except Exception as e:
                            logger.error(f"Error clearing {table} for session {session_id}: {str(e)}")
                            raise

        except Exception as e:
            logger.error(f"Failed to clear chat history for session {session_id}: {str(e)}")
            raise

