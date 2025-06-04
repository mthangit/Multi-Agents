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
RUN pip install --no-cache-dir -r requirements.txt

# Tuỳ chọn: copy mã nguồn sau cùng để tận dụng cache tối đa
# COPY . .

EXPOSE 8000
CMD ["bash"]
