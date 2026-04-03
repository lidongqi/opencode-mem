"""Configuration for mem0 memory plugin."""

from typing import Optional
from pydantic import BaseModel, Field


class Mem0Config(BaseModel):
    """Configuration for mem0 memory plugin."""

    api_key: Optional[str] = Field(
        default=None,
        description="Mem0 API key (for hosted version)"
    )
    
    # Self-hosted configuration
    vector_store: str = Field(
        default="chroma",
        description="Vector store to use (chroma, qdrant, pgvector, etc.)"
    )
    
    # LLM configuration
    llm_provider: str = Field(
        default="ollama",
        description="LLM provider to use"
    )
    
    llm_model: str = Field(
        default="glm-4.7-flash:latest",
        description="LLM model to use"
    )
    
    llm_base_url: Optional[str] = Field(
        default=None,
        description="LLM API base URL (for openai-compatible APIs)"
    )
    
    llm_api_key: Optional[str] = Field(
        default=None,
        description="LLM API key"
    )
    
    # Embedding configuration
    embedding_provider: str = Field(
        default="ollama",
        description="Embedding provider to use"
    )
    
    embedding_model: str = Field(
        default="nomic-embed-text-v2-moe:latest",
        description="Embedding model to use"
    )
    
    embedding_base_url: Optional[str] = Field(
        default=None,
        description="Embedding API base URL (for openai-compatible APIs)"
    )
    
    embedding_api_key: Optional[str] = Field(
        default=None,
        description="Embedding API key"
    )
    
    # Legacy Ollama configuration (for backward compatibility)
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL (legacy, use llm_base_url or embedding_base_url)"
    )
    
    # Chroma configuration
    chroma_path: str = Field(
        default="./mem0_chroma_db",
        description="Path to Chroma database"
    )
    
    # User configuration
    user_id: str = Field(
        default="default_user",
        description="Default user ID for memories"
    )
    
    # Memory configuration
    search_limit: int = Field(
        default=5,
        description="Number of memories to retrieve in search"
    )
    
    class Config:
        """Pydantic config."""
        env_prefix = "MEM0_"
