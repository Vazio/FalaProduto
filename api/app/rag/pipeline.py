"""RAG Pipeline for document ingestion and query processing."""
import logging
import os
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from pypdf import PdfReader
from docx import Document

from app.config import settings
from app.embeddings import get_embedding_provider
from app.retrieval import QdrantStore
from app.rerank import get_reranker
from app.llm import get_llm_provider

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Main RAG pipeline orchestrating ingestion and query processing."""
    
    def __init__(self):
        self.embedding_provider = get_embedding_provider()
        self.vector_store = QdrantStore()
        self.reranker = get_reranker()
        self.llm_provider = get_llm_provider()
        
        # Ensure Qdrant collection exists
        vector_dim = self.embedding_provider.get_dimension()
        self.vector_store.ensure_collection(vector_dim)
        
        logger.info("RAG Pipeline initialized successfully")
    
    def sanitize_query(self, query: str) -> tuple[str, bool]:
        """
        Sanitize and check query for malicious content.
        
        Returns:
            (sanitized_query, is_safe)
        """
        # Truncate to max length
        query = query[:settings.max_query_length]
        
        # Check for blocked terms
        query_lower = query.lower()
        blocked_terms = settings.get_blocked_terms_list()
        
        for term in blocked_terms:
            if term in query_lower:
                logger.warning(f"Blocked term detected in query: {term}")
                return query, False
        
        # Basic prompt injection patterns
        injection_patterns = [
            r"ignore\s+(previous|above|all)\s+instructions",
            r"you\s+are\s+(now|a)\s+\w+",
            r"system\s*:\s*",
            r"<\|im_start\|>",
            r"<\|endoftext\|>"
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, query_lower):
                logger.warning(f"Potential prompt injection detected: {pattern}")
                return query, False
        
        return query, True
    
    def extract_text_from_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from PDF with page information.
        
        Returns:
            List of dicts with 'text', 'page', 'title'
        """
        try:
            reader = PdfReader(file_path)
            title = Path(file_path).stem
            
            pages = []
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if text.strip():
                    pages.append({
                        "text": text,
                        "page": page_num,
                        "title": title
                    })
            
            logger.info(f"Extracted {len(pages)} pages from PDF: {title}")
            return pages
        
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {file_path}: {e}")
            return []
    
    def extract_text_from_docx(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from DOCX with paragraph information.
        
        Returns:
            List of dicts with 'text', 'page' (paragraph index), 'title'
        """
        try:
            doc = Document(file_path)
            title = Path(file_path).stem
            
            paragraphs = []
            for idx, para in enumerate(doc.paragraphs, start=1):
                text = para.text.strip()
                if text:
                    paragraphs.append({
                        "text": text,
                        "page": idx,  # Using paragraph index as "page"
                        "title": title
                    })
            
            logger.info(f"Extracted {len(paragraphs)} paragraphs from DOCX: {title}")
            return paragraphs
        
        except Exception as e:
            logger.error(f"Failed to extract text from DOCX {file_path}: {e}")
            return []
    
    def extract_text_from_txt(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from TXT file.
        
        Returns:
            List of dicts with 'text', 'page', 'title'
        """
        try:
            title = Path(file_path).stem
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                logger.warning(f"Empty TXT file: {title}")
                return []
            
            # Split by common page separators or large gaps
            # For simplicity, treat the whole file as one "page" or split by form feeds
            pages = []
            
            # Split by form feed character (if present) or by section markers
            if '\f' in content:
                # Split by form feed (page break)
                page_texts = content.split('\f')
            elif '═══' in content:
                # Split by section separators (like in our example files)
                page_texts = content.split('═══════════════════════════════════════════════════════════════')
            else:
                # Treat as single page
                page_texts = [content]
            
            for page_num, page_text in enumerate(page_texts, start=1):
                text = page_text.strip()
                if text:
                    pages.append({
                        "text": text,
                        "page": page_num,
                        "title": title
                    })
            
            logger.info(f"Extracted {len(pages)} pages from TXT: {title}")
            return pages
        
        except Exception as e:
            logger.error(f"Failed to extract text from TXT {file_path}: {e}")
            return []
    
    def chunk_text_hierarchical(
        self,
        pages: List[Dict[str, Any]],
        chunk_size: int = None,
        overlap: int = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text hierarchically, preserving headings and structure.
        
        Returns:
            List of chunks with metadata
        """
        chunk_size = chunk_size or settings.chunk_size
        overlap = overlap or settings.chunk_overlap
        
        all_chunks = []
        
        for page_data in pages:
            text = page_data["text"]
            page_num = page_data["page"]
            title = page_data["title"]
            
            # Simple heading detection (lines that are short and end with : or are all caps)
            lines = text.split("\n")
            current_section = ""
            current_text = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detect potential heading
                is_heading = (
                    len(line) < 80 and
                    (line.endswith(":") or line.isupper() or line.startswith("#"))
                )
                
                if is_heading and current_text:
                    # Process accumulated text
                    accumulated = " ".join(current_text)
                    chunks = self._split_text(accumulated, chunk_size, overlap)
                    
                    for idx, chunk in enumerate(chunks):
                        all_chunks.append({
                            "text": chunk,
                            "title": title,
                            "section": current_section,
                            "page": page_num,
                            "chunk_index": len(all_chunks)
                        })
                    
                    current_section = line
                    current_text = []
                else:
                    current_text.append(line)
            
            # Process remaining text
            if current_text:
                accumulated = " ".join(current_text)
                chunks = self._split_text(accumulated, chunk_size, overlap)
                
                for idx, chunk in enumerate(chunks):
                    all_chunks.append({
                        "text": chunk,
                        "title": title,
                        "section": current_section,
                        "page": page_num,
                        "chunk_index": len(all_chunks)
                    })
        
        logger.info(f"Created {len(all_chunks)} chunks from {len(pages)} pages")
        return all_chunks
    
    def _split_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split text into chunks with overlap."""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending in the last 100 chars
                last_period = text[max(start, end - 100):end].rfind(". ")
                if last_period != -1:
                    end = max(start, end - 100) + last_period + 1
            
            chunks.append(text[start:end].strip())
            start = end - overlap
        
        return chunks
    
    def ingest_documents(self, pdf_dir: str = None) -> Dict[str, Any]:
        """
        Ingest all documents from PDF directory.
        
        Returns:
            Stats dict with counts and timing
        """
        pdf_dir = pdf_dir or settings.pdf_dir
        start_time = time.time()
        
        logger.info(f"Starting document ingestion from {pdf_dir}")
        
        if not os.path.exists(pdf_dir):
            logger.error(f"PDF directory not found: {pdf_dir}")
            return {"error": f"Directory not found: {pdf_dir}"}
        
        # Find all PDF, DOCX and TXT files
        pdf_files = list(Path(pdf_dir).glob("*.pdf"))
        docx_files = list(Path(pdf_dir).glob("*.docx"))
        txt_files = list(Path(pdf_dir).glob("*.txt"))
        all_files = pdf_files + docx_files + txt_files
        
        if not all_files:
            logger.warning(f"No PDF, DOCX or TXT files found in {pdf_dir}")
            return {"error": "No documents found", "files_processed": 0}
        
        logger.info(f"Found {len(all_files)} documents to ingest ({len(pdf_files)} PDF, {len(docx_files)} DOCX, {len(txt_files)} TXT)")
        
        all_chunks = []
        
        # Extract text from all files
        for file_path in all_files:
            suffix = file_path.suffix.lower()
            if suffix == ".pdf":
                pages = self.extract_text_from_pdf(str(file_path))
            elif suffix == ".docx":
                pages = self.extract_text_from_docx(str(file_path))
            elif suffix == ".txt":
                pages = self.extract_text_from_txt(str(file_path))
            else:
                logger.warning(f"Unsupported file format: {file_path}")
                continue
            
            if pages:
                chunks = self.chunk_text_hierarchical(pages)
                all_chunks.extend(chunks)
        
        if not all_chunks:
            logger.warning("No text chunks extracted from documents")
            return {"error": "No content extracted", "files_processed": len(all_files)}
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(all_chunks)} chunks")
        texts = [chunk["text"] for chunk in all_chunks]
        embeddings = self.embedding_provider.embed_documents(texts)
        
        # Prepare metadata
        metadatas = []
        for chunk in all_chunks:
            metadatas.append({
                "doc_id": f"{chunk['title']}_{chunk['page']}",
                "title": chunk["title"],
                "section": chunk["section"],
                "page": chunk["page"],
                "source_path": chunk.get("source_path", ""),
                "chunk_index": chunk["chunk_index"]
            })
        
        # Upsert to Qdrant
        num_upserted = self.vector_store.upsert_documents(texts, embeddings, metadatas)
        
        elapsed = time.time() - start_time
        
        stats = {
            "files_processed": len(all_files),
            "chunks_created": len(all_chunks),
            "documents_upserted": num_upserted,
            "elapsed_seconds": round(elapsed, 2),
            "status": "success"
        }
        
        logger.info(f"Ingestion complete: {stats}")
        return stats
    
    def retrieve_and_generate(
        self,
        query: str,
        top_k: int = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main RAG pipeline: retrieve, rerank, generate answer with citations.
        
        Returns:
            Dict with answer, citations, usage stats
        """
        start_time = time.time()
        top_k = top_k or settings.top_k
        
        # Sanitize query
        query, is_safe = self.sanitize_query(query)
        
        if not is_safe:
            return {
                "answer": "Desculpe, a sua pergunta contém conteúdo bloqueado. Por favor, reformule a pergunta.",
                "citations": [],
                "usage": {"error": "blocked_content"},
                "status": "blocked"
            }
        
        # Embed query
        query_embedding = self.embedding_provider.embed_query(query)
        
        # Retrieve from Qdrant
        retrieval_start = time.time()
        retrieved_docs = self.vector_store.search(
            query_vector=query_embedding,
            top_k=top_k,
            filters=filters
        )
        retrieval_time = int((time.time() - retrieval_start) * 1000)
        
        if not retrieved_docs:
            return {
                "answer": "Não encontrei informação relevante na base de conhecimento para responder à sua pergunta. Por favor, tente reformular ou fazer uma pergunta sobre produtos de seguro.",
                "citations": [],
                "usage": {
                    "retrieval_time_ms": retrieval_time,
                    "num_retrieved": 0
                },
                "status": "no_results"
            }
        
        # Rerank
        rerank_start = time.time()
        reranked_docs = self.reranker.rerank(
            query=query,
            passages=retrieved_docs,
            top_k=settings.rerank_top_k
        )
        rerank_time = int((time.time() - rerank_start) * 1000)
        
        # Build prompt with context
        context = self._build_context(reranked_docs)
        prompt = self._build_prompt(query, context)
        system_prompt = self._get_system_prompt()
        
        # Generate answer
        llm_start = time.time()
        llm_response = self.llm_provider.generate(
            prompt=prompt,
            system_prompt=system_prompt
        )
        llm_time = int((time.time() - llm_start) * 1000)
        
        # Extract citations
        citations = self._extract_citations(reranked_docs)
        
        total_time = int((time.time() - start_time) * 1000)
        
        return {
            "answer": llm_response["answer"],
            "citations": citations,
            "usage": {
                "total_latency_ms": total_time,
                "retrieval_time_ms": retrieval_time,
                "rerank_time_ms": rerank_time,
                "llm_time_ms": llm_time,
                "tokens_prompt": llm_response["tokens_prompt"],
                "tokens_completion": llm_response["tokens_completion"],
                "model": llm_response["model"],
                "num_retrieved": len(retrieved_docs),
                "num_reranked": len(reranked_docs)
            },
            "status": "success"
        }
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt with guardrails."""
        return """És um assistente especializado em produtos de seguro. 

Regras importantes:
1. Responde APENAS com base nas fontes fornecidas no contexto
2. Se a pergunta estiver fora do âmbito de produtos de seguro, indica que não sabes
3. Inclui SEMPRE citações das fontes (título e página)
4. Evita linguagem especulativa ou inventar informação
5. Se não encontrares resposta no contexto, diz claramente que não tens essa informação

Formato da resposta:
## Resposta
[Tua resposta aqui]

## Fontes
• [Título do documento] (p. [número])
• [Título do documento] (p. [número])
"""
    
    def _build_context(self, docs: List[Dict[str, Any]]) -> str:
        """Build context string from retrieved documents."""
        context_parts = []
        
        for i, doc in enumerate(docs, 1):
            title = doc.get("title", "Documento")
            page = doc.get("page", 0)
            section = doc.get("section", "")
            text = doc.get("text", "")
            
            header = f"\n--- Fonte {i}: {title} (Página {page})"
            if section:
                header += f" - {section}"
            header += " ---\n"
            
            context_parts.append(header + text)
        
        context = "\n".join(context_parts)
        
        # Truncate if too long
        if len(context) > settings.max_context_chars:
            context = context[:settings.max_context_chars] + "\n\n[... contexto truncado ...]"
        
        return context
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Build the final prompt for the LLM."""
        return f"""Com base no seguinte contexto de documentos de produtos de seguro, responde à pergunta do utilizador.

CONTEXTO:
{context}

PERGUNTA: {query}

Responde de forma clara e estruturada, citando sempre as fontes."""
    
    def _extract_citations(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract citation information from documents."""
        citations = []
        seen = set()
        
        for doc in docs:
            # Create unique key to avoid duplicates
            key = (doc.get("title", ""), doc.get("page", 0))
            
            if key not in seen:
                citations.append({
                    "doc_id": doc.get("doc_id", ""),
                    "title": doc.get("title", ""),
                    "section": doc.get("section", ""),
                    "page": doc.get("page", 0),
                    "score": doc.get("rerank_score", doc.get("score", 0.0)),
                    "excerpt": doc.get("text", "")[:200] + "..."
                })
                seen.add(key)
        
        return citations[:3]  # Return top 3 distinct citations


