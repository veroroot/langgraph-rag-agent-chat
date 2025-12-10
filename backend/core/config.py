"""Application configuration using Pydantic Settings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    APP_NAME: str = "LangChain LangGraph Agent"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/rag_agent"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Vector Store
    VECTOR_STORE_TYPE: str = "pgvector"  # Options: pgvector, milvus
    VECTOR_DIMENSION: int = 1536  # OpenAI embedding dimension
    VECTOR_COLLECTION_NAME: str = "document_embeddings"
    
    # Embedding
    EMBEDDING_MODEL: str = "text-embedding-3-small"  # OpenAI model
    EMBEDDING_PROVIDER: str = "openai"  # Options: openai, local
    
    # LLM
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.0
    LLM_PROVIDER: str = "openai"
    
    # Provider API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Provider-specific model configurations
    # Format: {provider: [list of models]}
    PROVIDER_MODELS: dict[str, list[str]] = {
        "openai": [
            "gpt-5.1",
            "gpt-5",
            "gpt-5-mini",
            "gpt-5-nano"
        ],
        "anthropic": [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ],
    }
    
    # File Storage
    STORAGE_TYPE: str = "local"  # Options: local, s3
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE: int = 1000 * 1024 * 1024  # 1000MB
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".docx", ".txt", ".md"]

    # Milvus (optional)
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_USER: Optional[str] = None
    MILVUS_PASSWORD: Optional[str] = None
    MILVUS_DB_NAME: str = "default"
    MILVUS_CONSISTENCY_LEVEL: str = "Session"
    MILVUS_SECURE: bool = False
    
    # S3 (if STORAGE_TYPE is s3)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = None
    S3_BUCKET_NAME: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 30
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    JSON_LOGGING: str = "false"  # Set to "true" for structured JSON logs (recommended for production)
    
    # Agent Type
    AGENT_TYPE: str = "langgraph"  # Options: langchain, langgraph
    
    # LangGraph
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "rag_agent"
    POSTGRES_POOL_SIZE: int = 5
    PROJECT_NAME: str = "LangChain LangGraph Agent"
    CHECKPOINT_TABLES: list[str] = ["checkpoints", "checkpoint_blobs"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


def get_provider_api_key(provider: str) -> Optional[str]:
    """Get API key for a specific provider.
    
    Args:
        provider: Provider name (e.g., 'openai', 'anthropic')
        
    Returns:
        API key if available, None otherwise
    """
    key_map = {
        "openai": settings.OPENAI_API_KEY,
        "anthropic": settings.ANTHROPIC_API_KEY,
    }
    return key_map.get(provider.lower())


def is_provider_enabled(provider: str) -> bool:
    """Check if a provider is enabled (has API key configured).
    
    Args:
        provider: Provider name (e.g., 'openai', 'anthropic')
        
    Returns:
        True if provider has API key configured, False otherwise
    """
    api_key = get_provider_api_key(provider)
    return api_key is not None and api_key.strip() != ""


def get_enabled_providers() -> list[str]:
    """Get list of enabled providers (providers with API keys).
    
    Returns:
        List of enabled provider names
    """
    return [provider for provider in settings.PROVIDER_MODELS.keys() if is_provider_enabled(provider)]


def get_available_models_for_provider(provider: str) -> list[str]:
    """Get available models for a specific provider.
    
    Args:
        provider: Provider name
        
    Returns:
        List of model names for the provider, empty list if provider not found or not enabled
    """
    if not is_provider_enabled(provider):
        return []
    return settings.PROVIDER_MODELS.get(provider.lower(), [])


