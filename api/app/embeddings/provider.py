"""Embedding providers for document and query vectorization."""
import logging
from typing import List
from abc import ABC, abstractmethod

import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI, AzureOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        pass
    
    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get the dimension of the embeddings."""
        pass


class LocalEmbeddings(EmbeddingProvider):
    """Local embeddings using sentence-transformers."""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.local_embedding_model
        logger.info(f"Loading local embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self._dimension}")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        if not texts:
            return []
        
        # Batch encoding for efficiency
        embeddings = self.model.encode(
            texts,
            batch_size=8,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def get_dimension(self) -> int:
        """Get the dimension of the embeddings."""
        return self._dimension


class OpenAIEmbeddings(EmbeddingProvider):
    """OpenAI embeddings provider."""
    
    def __init__(self):
        self.model_name = settings.openai_embedding_model
        
        if settings.llm_provider == "azure" and settings.azure_openai_api_key:
            logger.info("Using Azure OpenAI for embeddings")
            self.client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint
            )
        else:
            logger.info("Using OpenAI for embeddings")
            self.client = OpenAI(api_key=settings.openai_api_key)
        
        # Dimension map for OpenAI models
        self.dimension_map = {
            "text-embedding-3-large": 3072,
            "text-embedding-3-small": 1536,
            "text-embedding-ada-002": 1536,
        }
        self._dimension = self.dimension_map.get(self.model_name, 1536)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        if not texts:
            return []
        
        # OpenAI has a limit of 2048 texts per request
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self.client.embeddings.create(
                input=batch,
                model=self.model_name
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        response = self.client.embeddings.create(
            input=[text],
            model=self.model_name
        )
        return response.data[0].embedding
    
    def get_dimension(self) -> int:
        """Get the dimension of the embeddings."""
        return self._dimension


def get_embedding_provider() -> EmbeddingProvider:
    """Factory function to get the configured embedding provider."""
    if settings.embeddings_provider == "openai":
        return OpenAIEmbeddings()
    else:
        return LocalEmbeddings()


