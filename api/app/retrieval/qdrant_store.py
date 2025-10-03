"""Qdrant vector store for document storage and retrieval."""
import logging
from typing import List, Dict, Any, Optional
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest
)

from app.config import settings

logger = logging.getLogger(__name__)


class QdrantStore:
    """Wrapper for Qdrant vector database operations."""
    
    def __init__(self):
        self.client = QdrantClient(url=settings.qdrant_url)
        self.collection_name = settings.qdrant_collection
        logger.info(f"Initialized Qdrant client pointing to {settings.qdrant_url}")
    
    def ensure_collection(self, vector_size: int):
        """Create collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name in collection_names:
                logger.info(f"Collection '{self.collection_name}' already exists")
                return
            
            logger.info(f"Creating collection '{self.collection_name}' with vector size {vector_size}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Collection '{self.collection_name}' created successfully")
        
        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
            raise
    
    def upsert_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ) -> int:
        """
        Upsert documents into Qdrant.
        
        Args:
            texts: List of text chunks
            embeddings: List of embedding vectors
            metadatas: List of metadata dicts with fields:
                - doc_id: unique document identifier
                - title: document title
                - section: section/heading name
                - page: page number
                - source_path: path to source file
        
        Returns:
            Number of documents upserted
        """
        if not texts or not embeddings or not metadatas:
            logger.warning("Empty input provided to upsert_documents")
            return 0
        
        if not (len(texts) == len(embeddings) == len(metadatas)):
            raise ValueError("texts, embeddings, and metadatas must have same length")
        
        points = []
        for i, (text, embedding, metadata) in enumerate(zip(texts, embeddings, metadatas)):
            point_id = str(uuid.uuid4())
            payload = {
                "text": text,
                "doc_id": metadata.get("doc_id", "unknown"),
                "title": metadata.get("title", ""),
                "section": metadata.get("section", ""),
                "page": metadata.get("page", 0),
                "source_path": metadata.get("source_path", ""),
                "chunk_index": metadata.get("chunk_index", i)
            }
            
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            ))
        
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Upserted {len(points)} documents to Qdrant")
            return len(points)
        
        except Exception as e:
            logger.error(f"Failed to upsert documents: {e}")
            raise
    
    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query_vector: Query embedding
            top_k: Number of results to return
            filters: Optional filters dict with keys like 'product', 'region'
        
        Returns:
            List of dicts with keys: id, text, score, metadata
        """
        try:
            # Build Qdrant filter if provided
            qdrant_filter = None
            if filters:
                conditions = []
                
                # Filter by product (title contains product name)
                if "product" in filters and filters["product"]:
                    conditions.append(
                        FieldCondition(
                            key="title",
                            match=MatchValue(value=filters["product"])
                        )
                    )
                
                # Add more filter conditions as needed
                if "doc_id" in filters and filters["doc_id"]:
                    conditions.append(
                        FieldCondition(
                            key="doc_id",
                            match=MatchValue(value=filters["doc_id"])
                        )
                    )
                
                if conditions:
                    qdrant_filter = Filter(must=conditions)
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=qdrant_filter,
                with_payload=True
            )
            
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "text": result.payload.get("text", ""),
                    "score": result.score,
                    "doc_id": result.payload.get("doc_id", ""),
                    "title": result.payload.get("title", ""),
                    "section": result.payload.get("section", ""),
                    "page": result.payload.get("page", 0),
                    "source_path": result.payload.get("source_path", "")
                })
            
            logger.info(f"Found {len(formatted_results)} results for query")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def count_documents(self) -> int:
        """Count total documents in collection."""
        try:
            result = self.client.count(collection_name=self.collection_name)
            return result.count
        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            return 0
    
    def delete_collection(self):
        """Delete the entire collection."""
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            logger.info(f"Deleted collection '{self.collection_name}'")
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise


