"""FastAPI application for Insurance Knowledge Base RAG system."""
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Try to import orjson for better performance, fallback to json
try:
    import orjson
    HAS_ORJSON = True
except ImportError:
    import json
    HAS_ORJSON = False

from app.config import settings
from app.rag import RAGPipeline

# Configure logging
if settings.log_format == "json":
    import json
    
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_obj = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
            }
            if record.exc_info:
                log_obj["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_obj)
    
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logging.root.handlers = [handler]

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Insurance Knowledge Base RAG API",
    description="RAG system for insurance product documentation with semantic search and chatbot",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (simple in-memory implementation)
rate_limit_store: Dict[str, list] = defaultdict(list)


def check_rate_limit(client_ip: str) -> bool:
    """Check if client has exceeded rate limit."""
    now = datetime.now()
    cutoff = now - timedelta(minutes=1)
    
    # Clean old requests
    rate_limit_store[client_ip] = [
        req_time for req_time in rate_limit_store[client_ip]
        if req_time > cutoff
    ]
    
    # Check limit
    if len(rate_limit_store[client_ip]) >= settings.rate_limit_per_minute:
        return False
    
    # Add current request
    rate_limit_store[client_ip].append(now)
    return True


# Initialize RAG pipeline
rag_pipeline: Optional[RAGPipeline] = None


@app.on_event("startup")
async def startup_event():
    """Initialize RAG pipeline on startup."""
    global rag_pipeline
    logger.info("Initializing RAG pipeline...")
    try:
        rag_pipeline = RAGPipeline()
        logger.info("RAG pipeline initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG pipeline: {e}")
        raise


# Request/Response models
class ChatRequest(BaseModel):
    """Chat request model."""
    query: str = Field(..., description="User query", min_length=1, max_length=500)
    top_k: Optional[int] = Field(None, description="Number of documents to retrieve", ge=1, le=20)
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters (product, region, etc.)")


class Citation(BaseModel):
    """Citation model."""
    doc_id: str
    title: str
    section: str
    page: int
    score: float
    excerpt: str


class Usage(BaseModel):
    """Usage statistics model."""
    total_latency_ms: int
    retrieval_time_ms: Optional[int] = None
    rerank_time_ms: Optional[int] = None
    llm_time_ms: Optional[int] = None
    tokens_prompt: Optional[int] = None
    tokens_completion: Optional[int] = None
    model: Optional[str] = None
    num_retrieved: Optional[int] = None
    num_reranked: Optional[int] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    answer: str
    citations: list[Citation]
    usage: Usage
    status: str


class IngestResponse(BaseModel):
    """Ingestion response model."""
    files_processed: int
    chunks_created: int
    documents_upserted: int
    elapsed_seconds: float
    status: str


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    qdrant_documents: int


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        doc_count = 0
        if rag_pipeline:
            doc_count = rag_pipeline.vector_store.count_documents()
        
        return HealthResponse(
            status="ok",
            timestamp=datetime.utcnow().isoformat(),
            qdrant_documents=doc_count
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest", response_model=IngestResponse)
async def ingest_documents(request: Request):
    """
    Ingest documents from the PDF directory.
    
    Reads all PDF and DOCX files from the configured directory,
    chunks them, generates embeddings, and stores in Qdrant.
    """
    # Check rate limit
    client_ip = request.client.host
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    if not rag_pipeline:
        raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
    
    try:
        logger.info("Starting document ingestion")
        result = rag_pipeline.ingest_documents()
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return IngestResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: Request, chat_request: ChatRequest):
    """
    Chat endpoint for querying the knowledge base.
    
    Performs RAG pipeline:
    1. Retrieves relevant documents using semantic search
    2. Re-ranks results for relevance
    3. Generates answer using LLM with citations
    """
    # Check rate limit
    client_ip = request.client.host
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    if not rag_pipeline:
        raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
    
    try:
        logger.info(f"Processing chat query: {chat_request.query[:100]}")
        
        result = rag_pipeline.retrieve_and_generate(
            query=chat_request.query,
            top_k=chat_request.top_k,
            filters=chat_request.filters
        )
        
        # Convert to response model
        citations = [Citation(**cite) for cite in result["citations"]]
        usage = Usage(**result["usage"])
        
        response = ChatResponse(
            answer=result["answer"],
            citations=citations,
            usage=usage,
            status=result["status"]
        )
        
        logger.info(f"Chat response generated in {usage.total_latency_ms}ms")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@app.get("/stats")
async def get_stats():
    """Get system statistics."""
    if not rag_pipeline:
        raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
    
    try:
        doc_count = rag_pipeline.vector_store.count_documents()
        
        return {
            "total_documents": doc_count,
            "collection_name": settings.qdrant_collection,
            "embeddings_provider": settings.embeddings_provider,
            "llm_model": settings.llm_model,
            "reranker": settings.reranker,
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Custom JSON response using orjson for better performance
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


