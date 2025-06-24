# EyeVi Agent - Hệ thống Multi-Agent RAG cho Mua sắm Mắt kính

EyeVi Agent là một hệ thống Multi-Agent sử dụng kỹ thuật Retrieval Augmented Generation (RAG) để hỗ trợ mua sắm mắt kính trực tuyến. Hệ thống này được thiết kế để tìm kiếm, tư vấn và xử lý đơn hàng mắt kính dựa trên các mô hình ngôn ngữ lớn (LLM).

## Tổng quan hệ thống

EyeVi Agent kết hợp nhiều agent chuyên biệt để tạo thành một hệ thống tư vấn mua sắm toàn diện:

- **Search Agent**: Tìm kiếm sản phẩm mắt kính bằng văn bản hoặc hình ảnh
- **Advisor Agent**: Tư vấn lựa chọn mắt kính phù hợp với người dùng
- **Order Agent**: Xử lý và theo dõi đơn hàng
- **Host Agent**: Quản lý tương tác với người dùng
- **Orchestrator Agent**: Điều phối luồng làm việc giữa các agent

## Cấu trúc thư mục

```
EyeVi_Agent/
├── app/                      # Mã nguồn chính của ứng dụng
│   ├── agents/               # Các agent trong hệ thống
│   │   ├── advisor_agent/    # Agent tư vấn lựa chọn mắt kính
│   │   ├── host_agent/       # Agent quản lý tương tác người dùng
│   │   ├── order_agent/      # Agent xử lý đơn hàng
│   │   ├── orchestrator_agent/ # Agent điều phối
│   │   └── search_agent/     # Agent tìm kiếm sản phẩm
│   ├── common/               # Các thành phần dùng chung
│   ├── config/               # Cấu hình hệ thống
│   ├── database/             # Kết nối và xử lý cơ sở dữ liệu
│   ├── hosts/                # Các host interface
│   ├── models/               # Các mô hình ML và định nghĩa dữ liệu
│   └── tools/                # Công cụ hỗ trợ cho các agent
├── data/                     # Dữ liệu và tài nguyên
├── .env                      # Biến môi trường (không nên commit)
├── .env.example              # Mẫu file biến môi trường
├── docker-compose.yml        # Cấu hình Docker Compose
├── Dockerfile                # Cấu hình Docker
├── requirements.txt          # Các thư viện phụ thuộc
├── run.py                    # Script khởi chạy chính
└── run.sh                    # Script hỗ trợ khởi chạy
```

## Các Agent và chức năng

### Search Agent

- **Chức năng**: Tìm kiếm sản phẩm mắt kính dựa trên văn bản hoặc hình ảnh
- **Công nghệ**: Sử dụng mô hình CLIP đã fine-tuning kết hợp với vector database Qdrant
- **Endpoint**: `/api/search/text` và `/api/search/image`
- **Khởi chạy riêng**: `python -m app.agents.search_agent.run_server --host 0.0.0.0 --port 8001 --reload`
- **[README.md](app/agents/search_agent/README.md)**: Tài liệu Search Agent

### Advisor Agent

- **Chức năng**: Tư vấn lựa chọn mắt kính phù hợp với người dùng
- **Công nghệ**: Sử dụng LLM để phân tích nhu cầu và đề xuất sản phẩm phù hợp
- **Endpoint**: `/api/advisor`
- **[README.md](app/agents/advisor_agent/README.md)**: Tài liệu Advidsor Agent

### Order Agent

- **Chức năng**: Xử lý đơn hàng, theo dõi trạng thái và cập nhật thông tin
- **Công nghệ**: Tích hợp với cơ sở dữ liệu MySQL để lưu trữ và quản lý đơn hàng
- **Endpoint**: `/api/order`
- **[README.md](app/agents/order_agent/README.md)**: Tài liệu Order Agent

### Host Agent

- **Chức năng**: Quản lý tương tác với người dùng, xử lý các yêu cầu ban đầu
- **Công nghệ**: Sử dụng LLM để hiểu và phân loại yêu cầu của người dùng
- **Endpoint**: `/api/host`
- **[README.md](app/agents/host_agent/README.md)**: Tài liệu Order Agent

## Cài đặt và Khởi chạy

### Yêu cầu hệ thống

- Python 3.12+
- Docker và Docker Compose (cho triển khai container)
- Google API key cho LLM

### Cài đặt thủ công

1. Sao chép file môi trường:
   ```bash
   cp .env.example .env
   ```

2. Cập nhật các biến môi trường trong file `.env`:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   ```

3. Cài đặt các thư viện phụ thuộc:
   ```bash
   pip install -r requirements.txt
   ```

4. Khởi chạy ứng dụng:
   ```bash
   python run.py
   ```
   
   hoặc
   
   ```bash
   ./run.sh
   ```

### Triển khai với Docker

1. Sao chép và cấu hình file môi trường:
   ```bash
   cp .env.example .env
   ```

2. Khởi chạy với Docker Compose:
   ```bash
   ./run_docker.sh
   ```
   
   hoặc
   
   ```bash
   docker-compose up -d
   ```

## Liên kết

- [Mã nguồn trên GitHub](https://github.com/mthangit/Multi-Agents/tree/main/EyeVi_Agent)

