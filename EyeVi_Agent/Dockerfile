FROM python:3.13-slim
WORKDIR /app

# Cài các công cụ hệ thống cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Cài thư viện base
RUN pip install --no-cache-dir \
    numpy \
    pydantic \
    python-dotenv \
    python-multipart \
    Pillow

# Cài thư viện backend
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    httpx \
    httpx-sse

# Cài thư viện ML
RUN pip install --no-cache-dir \
    torch>=2.0.0 \
    transformers>=4.38.0

# Cài vector DB
RUN pip install --no-cache-dir \
    qdrant-client>=1.7.0

# Cài thư viện Google (nặng nhất – để cuối)
RUN pip install --no-cache-dir --timeout=180 \
    google-generativeai \
    google-api-python-client \
    langchain-google-genai

# Tuỳ chọn: copy mã nguồn sau cùng để tận dụng cache tối đa
# COPY . .

EXPOSE 8000
CMD ["bash"]
