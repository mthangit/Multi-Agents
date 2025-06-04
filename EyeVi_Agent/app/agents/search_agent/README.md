# Search Agent

Agent tìm kiếm sản phẩm kính mắt sử dụng giao thức A2A, LangChain, LangGraph và Qdrant.

## Tổng quan

Search Agent là một trong những agent chuyên biệt trong hệ thống đa agent (multi-agent) của ứng dụng gợi ý kính mắt. Agent này có khả năng:

- Tìm kiếm sản phẩm kính mắt dựa trên văn bản
- Tìm kiếm sản phẩm kính mắt dựa trên hình ảnh
- Kết hợp phân tích khuôn mặt và sở thích người dùng để đề xuất sản phẩm phù hợp

## Kiến trúc

Search Agent được xây dựng dựa trên:

- **Giao thức A2A (Agent-to-Agent)**: Cho phép giao tiếp với Host Agent và các agent khác
- **LangChain/LangGraph**: Framework xây dựng chuỗi xử lý và luồng làm việc của agent
- **Qdrant**: Vector database lưu trữ embedding sản phẩm kính mắt
- **CLIP**: Mô hình embedding đa phương thức (multimodal) để xử lý văn bản và hình ảnh
- **Gemini**: Mô hình ngôn ngữ lớn (LLM) từ Google để xử lý ngôn ngữ tự nhiên

## Cài đặt

### Yêu cầu

- Python 3.10+
- Qdrant server (có thể chạy qua Docker)
- API key cho Google Gemini

### Cài đặt thư viện

```bash
# Tạo môi trường ảo
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc venv\Scripts\activate  # Windows

# Cài đặt các thư viện
pip install -r requirements.txt
```

### Tệp `requirements.txt`

```
langchain>=0.1.0
langchain-google-genai>=0.0.5
langgraph>=0.0.20
fastapi>=0.109.0
uvicorn>=0.27.0
qdrant-client>=1.7.0
pydantic>=2.6.0
torch>=2.0.0
transformers>=4.38.0
pillow>=10.0.0
python-multipart>=0.0.9
httpx>=0.26.0
httpx-sse>=0.4.0
```

### Thiết lập Qdrant

```bash
# Chạy Qdrant qua Docker
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_data:/qdrant/storage \
    qdrant/qdrant
```

### Thiết lập biến môi trường

```bash
# Thiết lập API key cho Google Gemini
export GOOGLE_API_KEY=your_api_key_here

# Thiết lập kết nối Qdrant (tùy chọn, mặc định là localhost:6333)
export QDRANT_HOST=localhost
export QDRANT_PORT=6333
```

## Khởi động Search Agent

```bash
# Điều hướng đến thư mục search_agent
cd /path/to/Backend/app/agents/search_agent

# Khởi động server
python run_server.py

# Hoặc với tham số tùy chỉnh
python run_server.py --host 0.0.0.0 --port 8001 --reload --debug
```

Sau khi khởi động, server sẽ chạy tại:
- API: http://localhost:8001
- OpenAPI docs: http://localhost:8001/docs
- Agent Card: http://localhost:8001/.well-known/agent.json

## Đăng ký với Host Agent

Để Host Agent có thể sử dụng Search Agent, bạn cần đăng ký Agent Card của Search Agent với Host Agent:

```python
from common.types import AgentCard
from hosts.multiagent.host_agent import HostAgent

# Khởi tạo Host Agent
host_agent = HostAgent(remote_agent_addresses=[...])

# Lấy Agent Card của Search Agent
from agents.search_agent import get_agent_card
search_agent_card = get_agent_card()

# Đăng ký Search Agent với Host Agent
host_agent.register_agent_card(search_agent_card)
```

## Cấu trúc thư mục

```
/search_agent/
├── __init__.py              # Export SearchAgent và get_agent_card
├── agent.py                 # Định nghĩa SearchAgent chính
├── search_service.py        # Refactor từ search.py, cung cấp dịch vụ tìm kiếm
├── run_server.py            # Script khởi động server
├── README.md                # Tài liệu hướng dẫn
├── prompts/                 # Chứa các prompt templates
│   ├── __init__.py
│   └── search_prompts.py
├── tools/                   # Các tool cho agent
│   ├── __init__.py
│   └── search_tools.py      # Wrapper cho ProductSearch
├── models/                  # Định nghĩa các model dữ liệu
│   ├── __init__.py
│   └── product.py           # Định nghĩa Product schema
├── chains/                  # Các chain logic 
│   ├── __init__.py
│   └── search_chain.py      # Chain xử lý tìm kiếm
└── api/                     # API A2A
    ├── __init__.py
    ├── card.py              # Agent Card definition
    └── endpoints.py         # Các endpoint cho A2A
```

## Luồng xử lý

1. **Host Agent** gửi yêu cầu tìm kiếm đến **Search Agent** thông qua giao thức A2A
2. **Search Agent** phân tích yêu cầu và sử dụng tool phù hợp (tìm kiếm bằng văn bản, hình ảnh, hoặc kết hợp)
3. **ProductSearch** sử dụng CLIP và Qdrant để tìm kiếm sản phẩm phù hợp
4. **Search Agent** định dạng kết quả và trả về cho **Host Agent** theo định dạng A2A
5. **Host Agent** hiển thị kết quả cho người dùng

## API Endpoints

### `POST /.well-known/agent.json`

Trả về Agent Card với thông tin về agent theo định dạng A2A.

### `POST /`

Endpoint chính xử lý các yêu cầu JSON-RPC từ Host Agent. Hỗ trợ các phương thức:

- `tasks/send`: Xử lý yêu cầu non-streaming
- `tasks/sendSubscribe`: Xử lý yêu cầu streaming qua Server-Sent Events (SSE)

## Debug và Logging

- Sử dụng tham số `--debug` khi khởi động server để bật chế độ debug
- Logs được ghi nhận thông qua Python logging
- Xem logs chi tiết để theo dõi quá trình tìm kiếm và giao tiếp A2A

## Tác giả

- Owner: [Your Name]
- Liên hệ: [Your Email]

## Giấy phép

[Specify License] 








Tiếp tục phát triển
Một số hướng phát triển tiếp theo có thể bao gồm:
    Thêm chức năng khác:
        Lọc sản phẩm theo giá
        Thêm tìm kiếm theo thương hiệu ưa thích
        Lưu trữ lịch sử tìm kiếm của người dùng
    Cải thiện hiệu suất:
        Tối ưu cache để giảm thời gian tìm kiếm
        Sử dụng batch processing cho các truy vấn phổ biến
    Tích hợp với Milvus:
        Theo đề cập ban đầu, bạn có thể thêm hỗ trợ cho Milvus để so sánh với Qdrant
    Cải thiện UX:
        Thêm thông tin phản hồi chi tiết hơn cho người dùng
        Tối ưu streaming để giảm độ trễ