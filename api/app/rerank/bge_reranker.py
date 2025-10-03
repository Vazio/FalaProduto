"""Re-ranking module for improving retrieval results."""
import logging
from typing import List, Dict, Any

from sentence_transformers import CrossEncoder

from app.config import settings

logger = logging.getLogger(__name__)


class BGEReranker:
    """BGE-based reranker using cross-encoder architecture."""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.local_reranker_model
        logger.info(f"Loading reranker model: {self.model_name}")
        self.model = CrossEncoder(self.model_name)
        logger.info("Reranker model loaded successfully")
    
    def rerank(
        self,
        query: str,
        passages: List[Dict[str, Any]],
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Rerank passages based on relevance to query.
        
        Args:
            query: User query
            passages: List of passage dicts with 'text' field
            top_k: Number of top results to return (None = all)
        
        Returns:
            Reranked list of passages with updated 'rerank_score' field
        """
        if not passages:
            return []
        
        if len(passages) == 1:
            passages[0]["rerank_score"] = 1.0
            return passages
        
        # Prepare query-passage pairs
        pairs = [[query, passage["text"]] for passage in passages]
        
        try:
            # Get reranking scores
            scores = self.model.predict(pairs)
            
            # Add rerank scores to passages
            for passage, score in zip(passages, scores):
                passage["rerank_score"] = float(score)
            
            # Sort by rerank score (descending)
            reranked = sorted(passages, key=lambda x: x["rerank_score"], reverse=True)
            
            # Return top_k if specified
            if top_k:
                reranked = reranked[:top_k]
            
            logger.info(f"Reranked {len(passages)} passages, returning top {len(reranked)}")
            return reranked
        
        except Exception as e:
            logger.error(f"Reranking failed: {e}, returning original order")
            return passages


class CohereReranker:
    """Cohere reranker (placeholder for optional integration)."""
    
    def __init__(self):
        # TODO: Implement Cohere reranker
        logger.warning("Cohere reranker not yet implemented, falling back to BGE")
        self.fallback = BGEReranker()
    
    def rerank(
        self,
        query: str,
        passages: List[Dict[str, Any]],
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """Rerank using Cohere API."""
        return self.fallback.rerank(query, passages, top_k)


def get_reranker():
    """Factory function to get the configured reranker."""
    if settings.reranker == "cohere" and settings.cohere_api_key:
        return CohereReranker()
    else:
        return BGEReranker()


