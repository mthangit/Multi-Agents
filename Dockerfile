FROM python:3.10-slim

WORKDIR /app

# Cài đặt các thư viện cơ bản và công cụ
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt các thư viện cơ bản
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Cài đặt các thư viện A2A và giao tiếp
RUN pip install --no-cache-dir \
    a2a-sdk>=0.1.0 \
    starlette>=0.27.0 \
    click>=8.0.0 \
    httpx>=0.26.0 \
    httpx-sse>=0.4.0 \
    protobuf

# Cài đặt các thư viện LangChain và LangGraph
RUN pip install --no-cache-dir \
    langchain>=0.1.0 \
    langchain-core \
    langgraph>=0.0.20 \
    langchain-community \
    langchain-google-genai>=0.0.5 \
    langchain-openai

# Cài đặt các thư viện FastAPI và backend
RUN pip install --no-cache-dir \
    fastapi>=0.109.0 \
    uvicorn>=0.27.0 \
    pydantic>=2.6.0 \
    pydantic-settings \
    python-multipart>=0.0.9 \
    python-dotenv==1.1.0

# Cài đặt các thư viện database
RUN pip install --no-cache-dir \
    qdrant-client>=1.7.0 \
    redis[hiredis]>=4.5.0 \
    mysql-connector-python \
    pymongo

# Cài đặt các thư viện xử lý PDF và embedding
RUN pip install --no-cache-dir \
    PyPDF2 \
    sentence-transformers \
    tiktoken

# Cài đặt các thư viện AI và ML
RUN pip install --no-cache-dir \
    torch>=2.0.0 \
    transformers>=4.38.0 \
    pillow>=10.0.0 \
    google-genai

# Cài đặt các thư viện xử lý text tiếng Việt
RUN pip install --no-cache-dir \
    regex \
    unicodedata2

# Cài đặt các thư viện bổ sung
RUN pip install --no-cache-dir \
    rank-bm25 \
    scikit-learn \
    structlog \
    asyncio \
    nest-asyncio

# Thiết lập biến môi trường
ENV PYTHONUNBUFFERED=1

# Port mặc định
EXPOSE 8080 10001 10002 10003 8001