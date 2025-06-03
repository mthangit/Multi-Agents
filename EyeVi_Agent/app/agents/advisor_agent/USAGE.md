# Hướng dẫn Sử dụng PDF RAG System

## 🏗️ Kiến trúc Mới (Tách biệt + Data Folder)

Hệ thống được tách thành 2 phần chính với thư mục `data/` mặc định:

1. **📥 Data Ingestion** (`ingest_data.py`) - Script nạp dữ liệu từ `data/` (chạy 1 lần)
2. **🤖 Chatbot** (`chatbot.py`) - Class xử lý queries (invoke mỗi lần chat)

## 🚀 Quy trình Sử dụng (Đơn giản hóa)

### Bước 1: Chuẩn bị Môi trường

```bash
# 1. Cài đặt dependencies
pip install -r requirements.txt

# 2. Khởi động Qdrant server
docker-compose up -d

# 3. Cấu hình Google API key
export GOOGLE_API_KEY="your_google_api_key_here"
```

### Bước 2: Setup Data Folder

```bash
# Tạo thư mục data (nếu chưa có)
mkdir data

# Đặt PDF files vào data/
cp your_files.pdf data/
# Hoặc tạo subfolder
mkdir data/research && cp research_papers.pdf data/research/
```

### Bước 3: Nạp Dữ liệu PDF (một lần)

```bash
# Nạp từ thư mục data/ (mặc định)
python ingest_data.py

# Hoặc với options
python ingest_data.py --clear     # Xóa dữ liệu cũ
python ingest_data.py --check     # Kiểm tra trạng thái
```

### Bước 4: Sử dụng Chatbot

```bash
# Setup guide (lần đầu)
python main.py setup

# Demo chatbot
python main.py demo

# Chế độ tương tác
python main.py interactive

# Kiểm tra trạng thái
python main.py check
```

## 📜 Chi tiết Commands

### 🔧 Data Ingestion Script

```bash
python ingest_data.py [options]
```

**Mặc định**: Tự động nạp từ thư mục `data/`

**Options:**
- `--clear`: Xóa collection cũ trước khi thêm
- `--force`: Force reprocess tất cả PDFs 
- `--check`: Chỉ kiểm tra prerequisites
- `--help`: Hiển thị trợ giúp

**Ví dụ:**

```bash
# Nạp tất cả PDF từ data/ (mặc định)
python ingest_data.py

# Nạp với xóa dữ liệu cũ
python ingest_data.py --clear

# Nạp từ path cụ thể
python ingest_data.py specific_folder/

# Kiểm tra hệ thống
python ingest_data.py --check
```

### 🤖 Main Application

```bash
python main.py [mode]
```

**Modes:**
- `setup`: Hướng dẫn setup lần đầu (khuyến nghị)
- `demo`: Demo chatbot với câu hỏi mẫu
- `interactive`: Chế độ chat tương tác
- `batch`: Demo xử lý batch queries
- `check`: Kiểm tra trạng thái dữ liệu
- `info`: Hiển thị thông tin hệ thống

## 💻 Sử dụng trong Code

### 1. Tạo Chatbot Instance

```python
from chatbot import PDFChatbot, create_chatbot

# Cách 1: Tạo instance mới
chatbot = PDFChatbot()

# Cách 2: Sử dụng factory function
chatbot = create_chatbot()

# Cách 3: Singleton instance
from chatbot import get_chatbot
chatbot = get_chatbot()
```

### 2. Sử dụng Invoke Method

```python
# Câu hỏi đơn giản
result = chatbot.invoke("Tài liệu này nói về gì?")
print(result["answer"])

# Với tham số tùy chỉnh
result = chatbot.invoke(
    "Phương pháp nghiên cứu là gì?",
    top_k=10,
    similarity_threshold=0.6,
    verbose=True
)

# Kiểm tra kết quả
if result["status"] == "success":
    print(f"Trả lời: {result['answer']}")
    print(f"Nguồn: {result['sources']}")
    print(f"Docs liên quan: {result['relevant_docs_count']}")
else:
    print(f"Lỗi: {result['error']}")
```

### 3. Batch Processing

```python
questions = [
    "Vấn đề chính là gì?",
    "Phương pháp được sử dụng?",
    "Kết luận quan trọng?"
]

results = chatbot.batch_invoke(questions, verbose=True)

for q, result in zip(questions, results):
    print(f"Q: {q}")
    print(f"A: {result['answer']}")
    print("-" * 50)
```

### 4. Health Check và Monitoring

```python
# Kiểm tra sức khỏe
health = chatbot.health_check()
print(f"Status: {health['status']}")

# Thống kê collection
stats = chatbot.get_collection_stats()
print(f"Vectors: {stats['vectors_count']}")

# Metadata từ response
result = chatbot.invoke("test question")
metadata = result["metadata"]
print(f"Model: {metadata['llm_model']}")
print(f"Embedding: {metadata['embedding_model']}")
```

## 🔄 Workflow trong Production

### 1. Setup lần đầu

```bash
# 1. Cài đặt và cấu hình
pip install -r requirements.txt
docker-compose up -d
export GOOGLE_API_KEY="your_key"

# 2. Nạp dữ liệu ban đầu
python ingest_data.py documents/ --clear

# 3. Test chatbot
python main.py check
python main.py demo
```

### 2. Cập nhật dữ liệu

```bash
# Khi có PDF mới, chỉ cần chạy ingest
python ingest_data.py new_documents/

# Hoặc thay thế hoàn toàn
python ingest_data.py all_documents/ --clear
```

### 3. Sử dụng hàng ngày

```python
# Trong application
from chatbot import get_chatbot

chatbot = get_chatbot()  # Singleton, tái sử dụng

# Xử lý user query
user_question = "..."
response = chatbot.invoke(user_question)
```

## 🎯 Use Cases

### 1. Web API

```python
from fastapi import FastAPI
from chatbot import get_chatbot

app = FastAPI()
chatbot = get_chatbot()

@app.post("/chat")
async def chat(query: str):
    result = chatbot.invoke(query)
    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "status": result["status"]
    }
```

### 2. Command Line Tool

```python
import sys
from chatbot import create_chatbot

def cli_chat():
    chatbot = create_chatbot()
    
    while True:
        query = input("Question: ")
        if query.lower() == 'exit':
            break
            
        result = chatbot.invoke(query)
        print(f"Answer: {result['answer']}")

if __name__ == "__main__":
    cli_chat()
```

### 3. Jupyter Notebook

```python
# Cell 1: Setup
from chatbot import create_chatbot
chatbot = create_chatbot()

# Cell 2: Test
result = chatbot.invoke("Tóm tắt tài liệu này")
display(result["answer"])

# Cell 3: Batch analysis
questions = ["Q1", "Q2", "Q3"]
results = chatbot.batch_invoke(questions)
```

## ⚙️ Configuration

### Runtime Configuration

```python
from config import Config

# Tùy chỉnh runtime
Config.TOP_K_DOCUMENTS = 10
Config.SIMILARITY_THRESHOLD = 0.6
Config.GEMINI_TEMPERATURE = 0.2

# Sử dụng với chatbot
result = chatbot.invoke("question", top_k=15)
```

### Environment Variables

```bash
export GOOGLE_API_KEY="your_key"
export GEMINI_MODEL="gemini-1.5-pro"
export QDRANT_URL="http://localhost:6333"
export COLLECTION_NAME="my_docs"
export TOP_K_DOCUMENTS="10"
export SIMILARITY_THRESHOLD="0.7"
```

## 🚨 Troubleshooting

### 1. Lỗi Collection rỗng

```bash
# Kiểm tra
python ingest_data.py --check

# Nạp dữ liệu
python ingest_data.py documents/
```

### 2. Lỗi Qdrant connection

```bash
# Kiểm tra Qdrant
curl http://localhost:6333/health
docker-compose ps

# Restart nếu cần
docker-compose restart
```

### 3. Lỗi Google API

```python
# Test API key
from chatbot import create_chatbot
chatbot = create_chatbot()
health = chatbot.health_check()
print(health)
```

## 📊 Monitoring

### Log Output

```
🤖 Khởi tạo PDF Chatbot...
🤖 Đang khởi tạo Gemini model: gemini-1.5-flash
📊 Collection ready: 1500 vectors
✅ Chatbot đã sẵn sàng!
```

### Performance Metrics

```python
import time

start = time.time()
result = chatbot.invoke("complex question")
end = time.time()

print(f"Response time: {end - start:.2f}s")
print(f"Docs retrieved: {result['total_retrieved_count']}")
print(f"Docs relevant: {result['relevant_docs_count']}")
```

---

💡 **Tips:**
- Chạy data ingestion khi có dữ liệu mới
- Sử dụng singleton pattern cho chatbot trong production
- Monitor response time và accuracy
- Backup collection before major updates 