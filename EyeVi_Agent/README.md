# Hệ thống Multi-Agent RAG

Hệ thống tìm kiếm sản phẩm dựa trên text hoặc ảnh đầu vào, sử dụng mô hình CLIP đã fine-tuning kết hợp với vector database Qdrant và công nghệ Multi-Agent của Google ADK.

## Tính năng

- Tìm kiếm sản phẩm bằng văn bản
- Tìm kiếm sản phẩm bằng ảnh
- Sử dụng model CLIP đã fine-tuning
- Kết nối với vector database Qdrant
- Hệ thống multi-agent với Google ADK
- API RESTful với FastAPI

## Cài đặt

### Yêu cầu

- Python 3.9+
- Qdrant server đã được cài đặt và khởi chạy
- Google API key

### Cài đặt các thư viện

```bash
pip install -r requirements.txt
```

### Cấu hình môi trường

Tạo file `.env` từ file `.env.example`:

```bash
cp .env.example .env
```

Chỉnh sửa các biến trong file `.env`:

```
GOOGLE_API_KEY=your_google_api_key_here
QDRANT_HOST=localhost
QDRANT_PORT=6333
VECTOR_SIZE=512
TEXT_COLLECTION_NAME=product_texts
IMAGE_COLLECTION_NAME=product_images
```

## Khởi chạy

```bash
python run.py
```

Hoặc với các tham số tùy chỉnh:

```bash
python run.py --host 0.0.0.0 --port 8000 --debug
```

## API Endpoints

### Tìm kiếm bằng văn bản

```
POST /api/search/text
```

Body:
```json
{
  "query": "áo thun màu đen",
  "filter_params": {
    "category": "clothing"
  }
}
```

### Tìm kiếm bằng ảnh

```
POST /api/search/image
```

Form-data:
- `image`: File ảnh
- `query` (tuỳ chọn): Mô tả bổ sung

### Reset Agent

```
POST /api/reset
```

## Cấu trúc dự án

```
.
├── requirements.txt
├── .env.example
├── run.py
├── README.md
└── src/
    ├── agents/
    │   ├── base_agent.py
    │   ├── text_search_agent.py
    │   ├── image_search_agent.py
    │   └── orchestrator.py
    ├── api/
    │   ├── app.py
    │   ├── endpoints.py
    │   └── models.py
    ├── config/
    │   └── settings.py
    ├── database/
    │   └── vector_store.py
    ├── models/
    │   └── clip_model.py
    ├── tools/
    │   └── search_tools.py
    └── utils/
        └── helpers.py
```

## Phát triển

### Thêm Agent mới

1. Tạo lớp agent mới kế thừa từ `BaseAgent`
2. Định nghĩa system prompt và tools cần thiết
3. Triển khai phương thức `process()`
4. Đăng ký agent với `AgentOrchestrator`

### Thêm Tool mới

1. Tạo lớp Tool mới kế thừa từ `BaseTool` của LangChain
2. Định nghĩa schema và phương thức `_run()`
3. Đăng ký tool với agent thích hợp 