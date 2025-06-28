# 🚀 **HOST AGENT API DOCUMENTATION**

## **⚡ Quick Reference**

### **Base URL**
```
http://localhost:8080
```

### **Main Endpoints**
```bash
# Chat (main endpoint)
POST /chat
curl -X POST "http://localhost:8080/chat" -F "message=Hello"

# With files
curl -X POST "http://localhost:8080/chat" \
  -F "message=Analyze this" -F "files=@image.jpg" -F "user_id=123"

# Health check
GET /health

# Agent status  
GET /agents/status

# Session management
POST /sessions/create
GET /sessions
GET /users/{user_id}/sessions

# Chat history
GET /sessions/{session_id}/history?user_id={user_id}
DELETE /sessions/{session_id}/history?user_id={user_id}
```

### **Required Environment**
```env
GOOGLE_API_KEY=your_google_api_key
```

### **Response Format**
```json
{
  "response": "AI response text",
  "agent_used": "Search Agent",
  "session_id": "abc-def-ghi",
  "status": "success",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## **📋 Overview**

Host Agent là orchestrator API để điều phối messages tới các specialized agents (Advisor, Search, Order) trong hệ thống multi-agent. API hỗ trợ chat với text, files, và real-time message logging vào MySQL.

**Base URL**: `http://localhost:8080`  
**Version**: `1.0.0`  
**Content Type**: `application/json` hoặc `multipart/form-data`

---

## **🏗️ Architecture**

```
User Request → Host Agent → [Orchestrator LLM] → Selected Agent → Response
                ↓
        [Redis + LangChain Memory]
                ↓
           [MySQL Logging]
```

### **Key Features**
- ✅ **Message Orchestration**: Tự động phân tích và route tới agent phù hợp
- ✅ **Multi-modal Support**: Text + files (images, documents)
- ✅ **Memory Management**: Redis + LangChain + MySQL triple storage
- ✅ **Real-time Logging**: Mỗi message tự động save vào MySQL
- ✅ **Session Management**: Support cho long conversations
- ✅ **Agent Health Monitoring**: Real-time status checking

---

## **📊 Data Models**

### **ChatResponse**
```json
{
  "response": "string",
  "agent_used": "string | null",
  "session_id": "string",
  "clarified_message": "string | null",
  "analysis": "string | null", 
  "data": "object | null",
  "status": "success",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### **HealthResponse**
```json
{
  "status": "healthy | unhealthy",
  "message": "string",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### **FileInfo** (Internal)
```json
{
  "name": "filename.jpg",
  "mime_type": "image/jpeg",
  "data": "base64_encoded_content"
}
```

---

## **🔗 API Endpoints**

### **1. Health Check**

#### `GET /`
**Description**: Basic health check endpoint

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "message": "Host Agent Server đang hoạt động tốt!",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### `GET /health`
**Description**: Detailed health check với agent status

**Response**: `200 OK`
```json
{
  "status": "healthy", 
  "message": "Tất cả services hoạt động tốt. Agents: {...}",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Error Response**: `500 Internal Server Error`
```json
{
  "detail": "Health check failed: connection error"
}
```

---

### **2. Chat Endpoint**

#### `POST /chat`
**Description**: Main endpoint để chat với system (text + files)

**Content-Type**: `multipart/form-data`

**Request Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message` | string | ✅ | Nội dung tin nhắn từ user |
| `user_id` | string | ❌ | ID người dùng (để track history) |
| `session_id` | string | ❌ | ID phiên chat (auto-generate nếu null) |
| `files` | List[UploadFile] | ❌ | Files đính kèm (images, docs) |

**Request Example** (with files):
```bash
curl -X POST "http://localhost:8080/chat" \
  -F "message=Tôi muốn tìm sản phẩm này" \
  -F "user_id=123" \
  -F "session_id=abc-def-ghi" \
  -F "files=@product_image.jpg"
```

**Request Example** (text only):
```bash
curl -X POST "http://localhost:8080/chat" \
  -F "message=Chào bạn, tôi cần tư vấn về sản phẩm" \
  -F "user_id=123"
```

**Response**: `200 OK`
```json
{
  "response": "Chào bạn! Tôi có thể giúp bạn tìm hiểu về các sản phẩm...",
  "agent_used": "Advisor Agent",
  "session_id": "abc-def-ghi-jkl",
  "clarified_message": "Tôi muốn tìm hiểu về sản phẩm iPhone 15 Pro Max",
  "analysis": "User đang tìm kiếm thông tin sản phẩm Apple",
  "data": {
    "product_ids": [123, 456],
    "category": "electronics"
  },
  "status": "success",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Error Response**: `500 Internal Server Error`
```json
{
  "detail": "Lỗi khi xử lý message: connection timeout"
}
```

---

### **3. Agent Management**

#### `GET /agents/status`
**Description**: Kiểm tra trạng thái tất cả agents

**Response**: `200 OK`
```json
{
  "status": "success",
  "agents": {
    "Advisor Agent": {
      "healthy": true,
      "url": "http://localhost:10001",
      "response_time": 0.15
    },
    "Search Agent": {
      "healthy": true, 
      "url": "http://localhost:10002",
      "response_time": 0.23
    },
    "Order Agent": {
      "healthy": false,
      "url": "http://localhost:10003", 
      "error": "Connection refused"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### **4. Session Management**

#### `POST /sessions/create`
**Description**: Tạo session ID mới

**Response**: `200 OK`
```json
{
  "status": "success",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Session mới đã được tạo thành công",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### `GET /sessions`
**Description**: Liệt kê tất cả active sessions

**Response**: `200 OK`
```json
{
  "status": "success",
  "active_sessions": 5,
  "sessions": [
    {
      "session_id": "abc-def-ghi",
      "created_at": "2024-01-15T10:00:00Z",
      "last_updated": "2024-01-15T10:25:00Z",
      "message_count": 12,
      "last_message_preview": "Cảm ơn bạn đã hỗ trợ tôi..."
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### `GET /users/{user_id}/sessions`
**Description**: Lấy tất cả sessions của user cụ thể

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | string | ID của user |

**Response**: `200 OK`
```json
{
  "status": "success",
  "user_id": "123",
  "total_sessions": 3,
  "sessions": [
    {
      "session_id": "abc-def-ghi",
      "created_at": "2024-01-15T10:00:00Z",
      "last_updated": "2024-01-15T10:25:00Z", 
      "message_count": 12,
      "last_message_preview": "Tôi muốn mua sản phẩm..."
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### **5. Chat History**

#### `GET /sessions/{session_id}/history`
**Description**: Lấy lịch sử chat cho session

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | ID của session |

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | string | ID của user (optional) |

**Response**: `200 OK`
```json
{
  "status": "success",
  "session_id": "abc-def-ghi",
  "user_id": "123",
  "messages": [
    {
      "role": "user",
      "content": "Chào bạn",
      "timestamp": "2024-01-15T10:00:00Z",
      "clarified_content": null
    },
    {
      "role": "assistant", 
      "content": "Xin chào! Tôi có thể giúp gì cho bạn?",
      "timestamp": "2024-01-15T10:00:05Z",
      "agent_used": "Host Agent"
    }
  ],
  "created_at": "2024-01-15T10:00:00Z",
  "last_updated": "2024-01-15T10:25:00Z",
  "total_messages": 12
}
```

**Empty Response**: `200 OK`
```json
{
  "status": "success",
  "session_id": "abc-def-ghi", 
  "user_id": "123",
  "messages": [],
  "message": "Không có lịch sử chat cho session này"
}
```

#### `DELETE /sessions/{session_id}/history`
**Description**: Xóa lịch sử chat cho session

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | ID của session |

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | string | ID của user (optional) |

**Response**: `200 OK`
```json
{
  "status": "success",
  "session_id": "abc-def-ghi",
  "user_id": "123",
  "message": "Đã xóa lịch sử chat thành công",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## **💾 MySQL Real-time Logging**

### **Database Schema**
```sql
CREATE TABLE message_history (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    session_id      VARCHAR(255) NOT NULL,
    user_id         BIGINT UNSIGNED NULL,
    sender_type     ENUM('user', 'host_agent', 'advisor_agent', 'search_agent', 'order_agent'),
    message_content TEXT NOT NULL,
    metadata        JSON NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### **Metadata Examples**
```json
{
  "clarified_content": "Tôi muốn mua iPhone 15 Pro Max",
  "files": ["product_image.jpg", "specs.pdf"],
  "agent_name": "Search Agent",
  "response_data": {
    "product_ids": [123, 456],
    "search_results": [...]
  },
  "analysis": "User đang tìm kiếm sản phẩm Apple cụ thể"
}
```

### **Automatic Logging**
- ✅ **Mỗi message** tự động save vào MySQL real-time
- ✅ **Rich metadata** including files, agent info, analysis
- ✅ **Graceful fallback** nếu MySQL down (không block chat)
- ✅ **Performance optimized** với connection pooling

---

## **🔧 Configuration**

### **Environment Variables**
```env
# Server
HOST=0.0.0.0
PORT=8080

# Google AI
GOOGLE_API_KEY=your_google_api_key

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# MySQL (New!)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=chat_db

# Agent URLs
ADVISOR_AGENT_URL=http://localhost:10001
SEARCH_AGENT_URL=http://localhost:10002
ORDER_AGENT_URL=http://localhost:10003
```

---

## **⚠️ Error Handling**

### **Common HTTP Status Codes**
| Code | Description | Example |
|------|-------------|---------|
| `200` | Success | Request processed successfully |
| `400` | Bad Request | Invalid parameters |
| `500` | Server Error | Internal processing error |

### **Error Response Format**
```json
{
  "detail": "Descriptive error message"
}
```

### **Common Errors**
- **Agent Unavailable**: System sẽ fallback về Host Agent
- **MySQL Down**: Messages vẫn save vào Redis/LangChain
- **Invalid File Format**: Files không được support sẽ bị skip
- **Session Not Found**: Tự động tạo session mới

---

## **🚀 Testing Examples**

### **Complete Test Flow**
```bash
# 1. Health check
curl -X GET "http://localhost:8080/health"

# 2. Create new session
curl -X POST "http://localhost:8080/sessions/create"

# 3. Simple chat
curl -X POST "http://localhost:8080/chat" \
  -F "message=Chào bạn, tôi cần tư vấn"

# 4. Chat with user ID và session ID
curl -X POST "http://localhost:8080/chat" \
  -F "message=Tôi muốn tìm iPhone 15 Pro Max" \
  -F "user_id=123" \
  -F "session_id=test-session-abc"

# 5. Continue conversation
curl -X POST "http://localhost:8080/chat" \
  -F "message=Còn màu nào khác?" \
  -F "user_id=123" \
  -F "session_id=test-session-abc"

# 6. Chat with file upload
curl -X POST "http://localhost:8080/chat" \
  -F "message=Phân tích sản phẩm trong hình này" \
  -F "user_id=123" \
  -F "session_id=test-session-abc" \
  -F "files=@product_image.jpg"

# 7. Check chat history
curl -X GET "http://localhost:8080/sessions/test-session-abc/history?user_id=123"

# 8. Check agent status
curl -X GET "http://localhost:8080/agents/status"

# 9. List user sessions
curl -X GET "http://localhost:8080/users/123/sessions"

# 10. Clear chat history
curl -X DELETE "http://localhost:8080/sessions/test-session-abc/history?user_id=123"
```

### **Python Testing Script**
```python
import requests
import json

BASE_URL = "http://localhost:8080"

def test_host_agent():
    # 1. Health check
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health: {response.json()}")
    
    # 2. Create session
    response = requests.post(f"{BASE_URL}/sessions/create")
    session_id = response.json()["session_id"]
    print(f"Session ID: {session_id}")
    
    # 3. Chat
    data = {
        "message": "Tôi cần tư vấn về kính cận thị",
        "user_id": "123",
        "session_id": session_id
    }
    response = requests.post(f"{BASE_URL}/chat", data=data)
    print(f"Chat Response: {response.json()}")
    
    # 4. Check history
    response = requests.get(f"{BASE_URL}/sessions/{session_id}/history?user_id=123")
    print(f"History: {response.json()}")

if __name__ == "__main__":
    test_host_agent()
```

### **JavaScript/Fetch Testing**
```javascript
const BASE_URL = 'http://localhost:8080';

async function testHostAgent() {
    try {
        // 1. Health check
        const healthResponse = await fetch(`${BASE_URL}/health`);
        console.log('Health:', await healthResponse.json());
        
        // 2. Create session
        const sessionResponse = await fetch(`${BASE_URL}/sessions/create`, {
            method: 'POST'
        });
        const sessionData = await sessionResponse.json();
        const sessionId = sessionData.session_id;
        
        // 3. Chat with FormData
        const formData = new FormData();
        formData.append('message', 'Chào bạn, tôi cần hỗ trợ');
        formData.append('user_id', '123');
        formData.append('session_id', sessionId);
        
        const chatResponse = await fetch(`${BASE_URL}/chat`, {
            method: 'POST',
            body: formData
        });
        console.log('Chat:', await chatResponse.json());
        
    } catch (error) {
        console.error('Test failed:', error);
    }
}

testHostAgent();
```

---

## **📊 Monitoring & Analytics**

### **MySQL Queries for Analytics**
```sql
-- Daily message stats
SELECT DATE(created_at) as date, 
       sender_type, 
       COUNT(*) as message_count
FROM message_history 
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY DATE(created_at), sender_type;

-- Top active sessions
SELECT session_id, 
       COUNT(*) as messages,
       MAX(created_at) as last_activity
FROM message_history 
GROUP BY session_id 
ORDER BY messages DESC 
LIMIT 10;

-- Agent usage distribution  
SELECT sender_type, 
       COUNT(*) as usage_count,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM message_history), 2) as percentage
FROM message_history 
WHERE sender_type != 'user'
GROUP BY sender_type;
```

---

## **🔒 Security Considerations**

- ✅ **Input Validation**: Tất cả inputs được validate
- ✅ **File Size Limits**: Files được giới hạn kích thước
- ✅ **SQL Injection Protection**: Sử dụng parameterized queries
- ✅ **Error Information**: Không expose sensitive data trong errors
- ⚠️ **Authentication**: Chưa implement (future feature)

---

## **🚧 Roadmap**

### **Planned Features**
- 🔐 **Authentication & Authorization** 
- 📈 **Advanced Analytics Dashboard**
- 🔄 **Webhook Support** for real-time updates
- 📱 **WebSocket Support** for real-time chat
- 🗂️ **File Storage Integration** (S3, CloudFlare)
- 🔍 **Full-text Search** trong chat history

---

## **🔗 Additional Resources**

### **Complete Setup Guide**
Xem [README.md](README.md) cho:
- Installation instructions
- Environment configuration  
- MySQL database setup
- Development guidelines

### **Source Code Structure**
```
host_agent/
├── main.py                 # FastAPI server
├── server/
│   ├── host_server.py      # Core orchestration logic
│   ├── a2a_client_manager.py # Agent communication
│   ├── mysql_message_history.py # Real-time logging
│   └── langchain_memory_adapter.py # Memory management
├── prompt/
│   └── root_prompt.py      # Orchestrator prompts
└── client/
    └── test_client.py      # Testing utilities
```

---

**📞 Support**: Liên hệ development team nếu có vấn đề kỹ thuật  
**📋 Version**: 1.0.0  
**🔄 Last Updated**: January 2024 