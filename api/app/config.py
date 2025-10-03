"""Configuration settings for the RAG API."""
import os
from typing import Literal
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM Configuration
    openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-4o-mini"
    azure_openai_api_version: str = "2024-02-01"
    
    llm_provider: Literal["openai", "azure"] = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1500
    
    # Embeddings Configuration
    embeddings_provider: Literal["local", "openai"] = "local"
    openai_embedding_model: str = "text-embedding-3-large"
    local_embedding_model: str = "BAAI/bge-large-en-v1.5"
    
    # Qdrant Configuration
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "insurance_products"
    vector_size: int = 1024
    
    # RAG Pipeline Configuration
    top_k: int = 6
    rerank_top_k: int = 3
    chunk_size: int = 800
    chunk_overlap: int = 150
    
    # Re-ranking Configuration
    reranker: Literal["local", "cohere"] = "local"
    cohere_api_key: str = ""
    local_reranker_model: str = "BAAI/bge-reranker-base"
    
    # Guardrails & Security
    max_context_chars: int = 12000
    max_query_length: int = 500
    blocked_terms: str = "segredo;credencial;senha;password;token;api_key;hack;inject"
    rate_limit_per_minute: int = 20
    
    # Observability
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"
    
    # Data Paths
    data_dir: str = "/data"
    pdf_dir: str = "/data/pdfs"
    groundtruth_dir: str = "/data/groundtruth"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_blocked_terms_list(self) -> list[str]:
        """Get list of blocked terms."""
        return [term.strip().lower() for term in self.blocked_terms.split(";") if term.strip()]


# Global settings instance
settings = Settings()


