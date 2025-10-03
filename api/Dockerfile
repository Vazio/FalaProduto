FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and set longer timeout
RUN pip install --upgrade pip setuptools wheel

# Copy requirements
COPY requirements.txt .

# Install dependencies with increased timeout and retries
# Install in stages: lightweight packages first, then ML packages
RUN pip install --default-timeout=300 --retries 5 \
    fastapi==0.109.0 \
    uvicorn[standard]==0.27.0 \
    pydantic==2.5.3 \
    pydantic-settings==2.1.0 \
    python-dotenv==1.0.0 \
    orjson==3.9.13 \
    python-multipart==0.0.6 \
    aiofiles==23.2.1 \
    tenacity==8.2.3

# Install document processing
RUN pip install --default-timeout=300 --retries 5 \
    pypdf==4.0.1 \
    python-docx==1.1.0

# Install LLM clients
RUN pip install --default-timeout=300 --retries 5 \
    openai==1.10.0 \
    tiktoken==0.5.2

# Install testing
RUN pip install --default-timeout=300 --retries 5 \
    pytest==7.4.4 \
    pytest-asyncio==0.23.3 \
    httpx==0.26.0

# Install Qdrant (small package)
RUN pip install --default-timeout=300 --retries 5 \
    qdrant-client==1.7.3

# Install ML packages (larger, more prone to timeout)
RUN pip install --default-timeout=600 --retries 5 \
    numpy==1.26.3

# Install sentence-transformers (largest package, most likely to timeout)
RUN pip install --default-timeout=900 --retries 5 \
    sentence-transformers==2.3.1

# Optional: Download models at build time (comment out if build is too slow)
# Models will be downloaded on first use if not pre-cached
# RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-large-en-v1.5'); SentenceTransformer('BAAI/bge-reranker-base')"

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


