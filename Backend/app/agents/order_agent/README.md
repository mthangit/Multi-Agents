# Order Management A2A Server

Hệ thống quản lý đơn hàng với khả năng giao tiếp Agent-to-Agent (A2A), được xây dựng bằng FastAPI, LangGraph và Redis.

## Tính năng chính

### 1. Chatbot thông minh
- Xử lý tin nhắn chat từ người dùng
- Hỗ trợ streaming response
- Tích hợp LangGraph cho xử lý phức tạp

### 2. Agent-to-Agent Communication (A2A)
- **Agent Registry**: Đăng ký và quản lý các agents trong hệ thống
- **Message Broker**: Route messages giữa các agents
- **Agent Discovery**: Tìm kiếm agents theo capabilities
- **Heartbeat System**: Theo dõi trạng thái agents
- **Broadcast Messages**: Gửi tin nhắn tới nhiều agents

### 3. Hệ thống Multi-Agent
- Hỗ trợ nhiều loại agents: Chatbot, Order Processor, Inventory Manager, Payment Processor, v.v.
- Giao tiếp đồng bộ và bất đồng bộ
- Load balancing và fault tolerance

## Kiến trúc hệ thống

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Chatbot       │    │  Order Processor│    │ Inventory Mgr   │
│   Agent         │    │   Agent         │    │   Agent         │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────┬───────────┴──────────┬───────────┘
                     │                      │
              ┌──────▼──────┐      ┌────────▼────────┐
              │  Message    │      │   Agent         │
              │  Broker     │      │   Registry      │
              │  (Redis)    │      │   (Redis)       │
              └─────────────┘      └─────────────────┘
```

## Yêu cầu hệ thống

- Python 3.8+
- Redis Server
- MySQL (tùy chọn)
- MongoDB (tùy chọn)

## Cài đặt

1. **Clone repository**
```bash
git clone <repository-url>
cd OrderAgents
```

2. **Tạo virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows
```

3. **Cài đặt dependencies**
```bash
pip install -r requirements.txt
```

4. **Cấu hình environment**
```bash
cp env.example .env
# Chỉnh sửa file .env với cấu hình của bạn
```

5. **Khởi động Redis Server**
```bash
redis-server
```

6. **Chạy ứng dụng**
```bash
python main.py
```

## API Endpoints

### Chatbot APIs
- `POST /chatbot/chat` - Gửi tin nhắn chat
- `POST /chatbot/chat` (với `stream=true`) - Streaming chat

### A2A APIs

#### Agent Management
- `POST /a2a/register` - Đăng ký agent
- `DELETE /a2a/unregister/{agent_id}` - Hủy đăng ký agent
- `GET /a2a/agents` - Danh sách tất cả agents
- `GET /a2a/agents/{agent_id}` - Thông tin chi tiết agent

#### Agent Discovery
- `POST /a2a/discover` - Tìm kiếm agents theo điều kiện

#### Messaging
- `POST /a2a/send` - Gửi message tới agent khác
- `POST /a2a/broadcast` - Broadcast message
- `POST /a2a/receive` - Nhận message (webhook)

#### System
- `POST /a2a/heartbeat` - Cập nhật heartbeat
- `GET /a2a/health` - Health check
- `GET /a2a/stats` - Thống kê hệ thống
- `GET /a2a-status` - Trạng thái A2A agent

## Sử dụng A2A System

### 1. Đăng ký Agent

```python
import requests

agent_data = {
    "agent_info": {
        "agent_id": "my_agent_001",
        "name": "My Custom Agent",
        "agent_type": "custom",
        "description": "Agent xử lý tác vụ đặc biệt",
        "capabilities": [
            {
                "name": "process_data",
                "description": "Xử lý dữ liệu",
                "input_schema": {"type": "object", "properties": {"data": {"type": "string"}}},
                "output_schema": {"type": "object", "properties": {"result": {"type": "string"}}}
            }
        ],
        "endpoint": "http://localhost:8001",
        "status": "active"
    }
}

response = requests.post("http://localhost:8000/a2a/register", json=agent_data)
print(response.json())
```

### 2. Tìm kiếm Agents

```python
# Tìm tất cả chatbot agents
discovery_data = {
    "agent_type": "chatbot",
    "status": "active"
}

response = requests.post("http://localhost:8000/a2a/discover", json=discovery_data)
agents = response.json()["agents"]
print(f"Found {len(agents)} chatbot agents")
```

### 3. Gửi Message giữa Agents

```python
message_data = {
    "message_id": "msg_001",
    "from_agent_id": "my_agent_001",
    "to_agent_id": "chatbot_agent_id",
    "message_type": "request",
    "capability": "chat",
    "payload": {
        "message": "Xin chào, tôi cần hỗ trợ đặt hàng",
        "session_id": "session_123"
    },
    "correlation_id": "corr_001"
}

response = requests.post("http://localhost:8000/a2a/send", json=message_data)
result = response.json()
print(f"Response: {result}")
```

### 4. Broadcast Message

```python
broadcast_data = {
    "from_agent_id": "my_agent_001",
    "message_type": "notification",
    "payload": {
        "event": "system_maintenance",
        "message": "Hệ thống sẽ bảo trì trong 30 phút"
    },
    "target_agent_types": ["chatbot", "order_processor"]
}

response = requests.post("http://localhost:8000/a2a/broadcast", json=broadcast_data)
result = response.json()
print(f"Broadcast sent to {result['data']['broadcast_count']} agents")
```

## Agent Capabilities

Agent hiện tại (Chatbot) hỗ trợ các capabilities sau:

### 1. `chat`
- **Mô tả**: Xử lý tin nhắn chat từ người dùng
- **Input**: `{"message": "string", "session_id": "string"}`
- **Output**: `{"response": "string", "session_id": "string"}`

### 2. `process_order`
- **Mô tả**: Xử lý yêu cầu đặt hàng
- **Input**: `{"message": "string", "customer_info": "object"}`
- **Output**: `{"order_id": "string", "status": "string", "details": "object"}`

### 3. `get_order_status`
- **Mô tả**: Kiểm tra trạng thái đơn hàng
- **Input**: `{"order_id": "string"}`
- **Output**: `{"order_id": "string", "status": "string", "details": "object"}`

## Mở rộng hệ thống

### Tạo Agent mới

1. **Implement Agent Class**
```python
from src.a2a.agent_adapter import ChatbotA2AAdapter

class MyCustomAgent:
    def __init__(self):
        self.adapter = ChatbotA2AAdapter(...)
    
    async def handle_custom_capability(self, payload):
        # Xử lý logic của bạn
        return {"result": "processed"}
```

2. **Đăng ký Capabilities**
```python
broker = await get_message_broker()
broker.register_handler("my_capability", agent.handle_custom_capability)
```

3. **Đăng ký vào Registry**
```python
await agent.adapter.register_agent()
```

## Monitoring và Debugging

### Health Check
```bash
curl http://localhost:8000/a2a/health
```

### System Stats
```bash
curl http://localhost:8000/a2a/stats
```

### A2A Status
```bash
curl http://localhost:8000/a2a-status
```

### Logs
- Application logs: `app.log`
- Debug logs: `debug_logs/`

## Cấu hình nâng cao

### Redis Configuration
```bash
# .env file
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Heartbeat Timeout
Mặc định: 60 giây. Có thể thay đổi trong `src/a2a/registry.py`

### Message Timeout
Mặc định: 30 giây. Có thể thay đổi khi gửi message

## Troubleshooting

### Redis Connection Issues
```bash
# Kiểm tra Redis running
redis-cli ping

# Kiểm tra logs
tail -f app.log
```

### Agent Registration Failed
- Kiểm tra Redis connection
- Verify agent_id không trùng lặp
- Check capabilities schema

### Message Delivery Issues
- Verify target agent đang online
- Check endpoint configuration
- Monitor logs cho errors

## Contributing

1. Fork repository
2. Tạo feature branch
3. Implement changes
4. Add tests
5. Submit pull request

## License

MIT License - see LICENSE file for details 