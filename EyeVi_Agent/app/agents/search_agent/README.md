# Search Agent

Agent tìm kiếm sản phẩm kính mắt sử dụng A2A protocol.

## Tính năng

- Tìm kiếm sản phẩm bằng văn bản
- Tìm kiếm sản phẩm bằng hình ảnh
- Tìm kiếm sản phẩm dựa trên phân tích khuôn mặt
- Hỗ trợ giao thức A2A (Agent-to-Agent)


## 📖 Tài liệu chi tiết

- **[README_A2A.md](docs/README_A2A.md)**: Tài liệu A2A cho advisor agent
- **[system.md](docs/system.md)**: Tài liệu chi tiết hệ thống search agent


## Cài đặt

```bash
# Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt
```

## Sử dụng

### Chạy agent

```bash
python server.py
```

### Sử dụng client để tương tác với agent

```bash
# Chế độ tương tác
python client.py chat

# Chế độ demo với các câu hỏi mẫu
python client.py demo

# Gửi câu hỏi trực tiếp
python client.py "Tôi cần một cặp kính râm chống UV"
```

### Tìm kiếm bằng hình ảnh

Có hai cách để tìm kiếm sản phẩm bằng hình ảnh:

#### 1. Sử dụng chế độ tương tác

Trong chế độ tương tác (`python client.py chat`), bạn có thể sử dụng lệnh `image` để gửi hình ảnh:

```
image <đường_dẫn_đến_ảnh> [mô_tả_tùy_chọn]
```

Ví dụ:
```
image /path/to/glasses.jpg Tôi muốn tìm kính giống mẫu này
```

#### 2. Sử dụng công cụ kiểm tra tìm kiếm ảnh

```bash
python image_search_test.py /path/to/image.jpg -d "Mô tả về ảnh" -u http://localhost:10002
```

Tham số:
- Đường dẫn đến file ảnh (bắt buộc)
- `-d`, `--description`: Mô tả về ảnh (tùy chọn)
- `-u`, `--url`: URL của agent (mặc định: http://localhost:10002)

### Cấu trúc message trong A2A

Khi gửi tin nhắn có hình ảnh, client sẽ tạo một message với nhiều parts:

```json
{
  "message": {
    "role": "user",
    "parts": [
      {
        "kind": "text",
        "text": "Mô tả về ảnh"
      },
      {
        "kind": "file",
        "file": {
          "name": "image.jpg",
          "mimeType": "image/jpeg",
          "bytes": "base64_encoded_data"
        }
      }
    ],
    "messageId": "unique_id"
  }
}
```

## Luồng xử lý tìm kiếm bằng hình ảnh

1. Client gửi message chứa text và/hoặc hình ảnh đến agent
2. Agent executor trích xuất dữ liệu từ message
3. Dữ liệu được chuyển đến search agent để xử lý
4. Search agent phân tích hình ảnh và tìm kiếm sản phẩm phù hợp
5. Kết quả được trả về cho client

## Phát triển

### Cấu trúc thư mục

```
search_agent/
├── a2a_wrapper/          # Wrapper cho A2A protocol
│   └── a2a_agent_executor.py
├── agent/                # Core agent logic
│   └── agent.py
├── chains/               # LangGraph chains
│   └── search_graph.py
├── nodes/                # LangGraph nodes
├── api/                  # API endpoints
├── client.py             # A2A client
├── image_search_test.py  # Tool to test image search
├── server.py             # A2A server
└── README.md
```

### Mở rộng

- Thêm hỗ trợ cho các định dạng ảnh khác
- Cải thiện phân tích hình ảnh
- Thêm khả năng tìm kiếm theo nhiều ảnh