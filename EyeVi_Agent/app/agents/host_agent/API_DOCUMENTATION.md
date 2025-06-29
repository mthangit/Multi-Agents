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

# Database Configuration (Optional - nếu không có sẽ fallback về Redis)
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=eyevi_agent

# Redis Configuration (Optional - có default values)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Server Configuration (Optional)
HOST=0.0.0.0
PORT=8080
```

### **Response Format**
```json
{
  "response": "AI response text",
  "agent_used": "Search Agent",
  "session_id": "abc-def-ghi",
  "clarified_message": "Clarified user message",
  "analysis": "Analysis of user request",
  "data": [...],
  "user_info": {...},
  "orders": [...],
  "extracted_product_ids": ["12345"],
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
- ✅ **Product ID Extraction**: Tự động trích xuất product ID khi user muốn mua hàng
- ✅ **Seamless Response**: Không nhắc đến agent source trong response
- ✅ **File Upload Support**: Hỗ trợ multiple files với đa dạng format
- ✅ **Pagination**: Chat history với pagination (50 messages gần nhất)

---

## **🎯 Advanced Features**

### **Product ID Extraction & Context Clarification**

Hệ thống tự động trích xuất product ID và làm rõ context khi user muốn mua hàng:

**Workflow**:
1. **User tìm kiếm**: "Tìm kính cận thị cho nam"
   → Search Agent trả về sản phẩm có ID: 12345

2. **User muốn mua**: "Tôi muốn mua sản phẩm đó"
   → System tự động:
   - Quét context để tìm sản phẩm với ID: 12345
   - Làm rõ: "Tôi muốn mua Kính cận Ray-Ban với ID: 12345"
   - Gửi tới Order Agent với product ID đính kèm

**Context Clarification Examples**:
- `"sản phẩm đó"` → `"Kính cận Ray-Ban RB2140"`
- `"tôi muốn mua nó"` → `"tôi muốn mua Kính cận Ray-Ban với ID: 12345"`
- `"địa chỉ đó"` → `"123 Đường ABC, Quận 1, TP.HCM"`

**Response Example**:
```json
{
  "response": "Tôi đã thêm sản phẩm vào giỏ hàng của bạn...",
  "clarified_message": "Tôi muốn mua Kính cận Ray-Ban với ID: 12345",
  "extracted_product_ids": ["12345"],
  "agent_used": "Order Agent",
  "data": [{"product_id": "12345", "quantity": 1}]
}
```

### **Agent Response Policy**

**Nguyên tắc**: Tuyệt đối không nhắc đến agent trong response tới user

**❌ KHÔNG làm**:
- "Search Agent đã tìm thấy..."
- "Theo Advisor Agent..."
- "Như đã được trả lời bởi..."

**✅ ĐÚNG cách**:
- "Tôi đã tìm thấy..."
- "Dựa trên thông tin..."
- "Về sản phẩm này..."

### **File Upload Support**

**Supported File Types**:
- **Images**: JPG, JPEG, PNG, GIF, WebP, BMP
- **Documents**: PDF, TXT, DOC, DOCX
- **Data**: JSON, CSV, XML
- **Others**: Tự động detect MIME type

**File Size Limits**:
- Single file: 10MB
- Total upload: 50MB
- Max files per request: 10

**Processing**:
- Files được encode thành base64
- Tự động detect MIME type
- Support multiple files trong một request

---

## **📊 Data Models**

### **ChatResponse**
```json
{
  "response": "string",                    // Câu trả lời chính từ system
  "agent_used": "string | null",          // Agent đã xử lý (tracking only)
  "session_id": "string",                 // Session ID
  "clarified_message": "string | null",   // Message đã được làm rõ
  "analysis": "string | null",            // Phân tích request
  "data": "array | null",                 // Dữ liệu structured (products, etc.)
  "user_info": "object | null",           // Thông tin user (từ Order Agent)
  "orders": "array | null",               // Danh sách đơn hàng từ Order Agent
  "extracted_product_ids": "array | null", // Product IDs được trích xuất
  "status": "string",                     // "success" | "error"
  "timestamp": "string"                   // ISO 8601 timestamp
}
```

**Field Descriptions**:
- `response`: Câu trả lời chính (không nhắc đến agent source)
- `agent_used`: Agent đã xử lý (chỉ cho tracking, không hiển thị cho user)
- `clarified_message`: Message đã được làm rõ (thay đại từ bằng tên cụ thể)
- `data`: Dữ liệu structured từ agents (products, search results, etc.)
- `user_info`: Thông tin user profile từ Order Agent
- `orders`: Danh sách đơn hàng từ Order Agent
- `extracted_product_ids`: Product IDs khi user muốn mua hàng

### **HealthResponse**
```json
{
  "status": "healthy | unhealthy",
  "message": "string",
  "timestamp": "string"
}
```

### **AgentStatusResponse**
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
  "timestamp": "string"
}
```

### **ChatHistoryResponse**
```json
{
  "status": "success",
  "session_id": "string",
  "user_id": "string",
  "messages": [
    {
      "role": "user | assistant",
      "content": "string",
      "timestamp": "string",
      "clarified_content": "string | null",
      "agent_used": "string | null"
    }
  ],
  "created_at": "string",
  "last_updated": "string", 
  "total_messages": 100,
  "returned_messages": 50
}
```

### **SessionInfo**
```json
{
  "session_id": "string",
  "created_at": "string",
  "last_updated": "string",
  "message_count": 12,
  "last_message_preview": "string"
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
| `files` | List[UploadFile] | ❌ | Files đính kèm (max 10 files, 10MB/file) |

**File Upload Constraints**:
- Max file size: 10MB per file
- Max total upload: 50MB
- Max files per request: 10
- Supported formats: images, documents, data files

**Request Example** (with files):
```bash
curl -X POST "http://localhost:8080/chat" \
  -F "message=Tôi muốn tìm sản phẩm này" \
  -F "user_id=123" \
  -F "session_id=abc-def-ghi" \
  -F "files=@product_image.jpg" \
  -F "files=@specs.pdf"
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
  "data": [
    {
      "product_id": "123",
      "name": "iPhone 15 Pro Max",
      "price": "29990000"
    }
  ],
  "user_info": {
    "user_id": "123",
    "name": "Nguyễn Văn A",
    "phone": "0901234567"
  },
  "orders": [
    {
      "order_id": "ORD001",
      "status": "pending",
      "total": "29990000"
    }
  ],
  "extracted_product_ids": ["123"],
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

**Error Response**: `413 Payload Too Large`
```json
{
  "detail": "File upload exceeds size limit. Max 10MB per file, 50MB total."
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

**Error Response**: `500 Internal Server Error`
```json
{
  "detail": "Failed to get agents status: connection error"
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

**Error Response**: `500 Internal Server Error`
```json
{
  "detail": "Failed to create new session: internal error"
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

**Error Response**: `500 Internal Server Error`
```json
{
  "detail": "Failed to list active sessions: internal error"
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

**Error Response**: `500 Internal Server Error`
```json
{
  "detail": "Failed to get user sessions for 123: database error"
}
```

---

### **5. Chat History**

#### `GET /sessions/{session_id}/history`
**Description**: Lấy lịch sử chat cho session (50 messages gần nhất)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | ID của session |

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | string | ID của user (optional, recommended) |

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
  "total_messages": 100,
  "returned_messages": 50
}
```

**Empty Response**: `200 OK`
```json
{
  "status": "success",
  "session_id": "abc-def-ghi",
  "user_id": "123",
  "messages": [],
  "message": "Không có lịch sử chat cho session này",
  "total_messages": 0,
  "returned_messages": 0
}
```

**Error Response**: `500 Internal Server Error`
```json
{
  "detail": "Failed to get chat history for session abc-def-ghi: database error"
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
| `user_id` | string | ID của user (optional, recommended) |

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

**Error Response**: `500 Internal Server Error`
```json
{
  "detail": "Failed to clear chat history for session abc-def-ghi: database error"
}
```

---

## **🛠️ Error Handling**

### **HTTP Status Codes**
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `413` - Payload Too Large (file upload limits)
- `422` - Unprocessable Entity (validation errors)
- `500` - Internal Server Error

### **Error Response Format**
```json
{
  "detail": "Detailed error message in Vietnamese",
  "error_code": "ERROR_CODE", // Optional
  "context": {               // Optional
    "session_id": "abc-def",
    "user_id": "123"
  }
}
```

### **Common Error Scenarios**

**File Upload Errors**:
```bash
# File too large
{"detail": "File upload exceeds size limit. Max 10MB per file, 50MB total."}

# Too many files
{"detail": "Too many files. Maximum 10 files per request."}

# Unsupported file type
{"detail": "Unsupported file type: .exe"}
```

**Agent Connection Errors**:
```bash
# Agent unavailable
{"detail": "Search Agent không khả dụng. Vui lòng thử lại sau."}

# Timeout
{"detail": "Request timeout khi kết nối với Advisor Agent"}
```

**Database Errors**:
```bash
# MySQL connection failed
{"detail": "Không thể kết nối database. Messages sẽ được lưu tạm thời."}

# Redis connection failed  
{"detail": "Redis connection failed. Chat history có thể bị mất."}
```

---

## **🚀 Getting Started**

### **1. Environment Setup**
```bash
# Clone repository
git clone <repository-url>
cd host_agent

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp env.example .env
# Edit .env với các giá trị phù hợp
```

### **2. Database Setup (Optional)**
```bash
# Setup MySQL (optional - fallback to Redis if not available)
mysql -u root -p < setup_mysql.sql

# Redis sẽ được auto-setup nếu available
```

### **3. Start Server**
```bash
# Production
python main.py

# Development
python main.py --reload

# Custom host/port
HOST=127.0.0.1 PORT=8081 python main.py
```

### **4. Test API**
```bash
# Basic health check
curl http://localhost:8080/health

# Simple chat
curl -X POST "http://localhost:8080/chat" -F "message=Hello"

# Chat with file
curl -X POST "http://localhost:8080/chat" \
  -F "message=Phân tích hình ảnh này" \
  -F "files=@image.jpg"
```

---

## **📈 Performance & Limitations**

### **Performance Metrics**
- **Response Time**: < 2s cho text-only requests
- **File Upload**: < 5s cho files dưới 5MB
- **Concurrent Users**: Support 100+ concurrent sessions
- **Memory Usage**: ~500MB RAM baseline
- **Storage**: Redis + MySQL dual storage

### **Rate Limits**
- **Requests**: 100 requests/minute per IP
- **File Upload**: 50MB total/request
- **Session Limit**: 1000 active sessions
- **History**: 50 messages per history request

### **Scalability**
- **Horizontal**: Có thể deploy multiple instances
- **Load Balancer**: Support load balancing
- **Database**: MySQL cluster support
- **Caching**: Redis cluster support

---

## **🔐 Security Considerations**

### **File Upload Security**
- File type validation
- Size limits enforced
- Malware scanning (recommend external service)
- Base64 encoding for safe transmission

### **Data Privacy**
- User IDs không expose personal information
- Chat history encrypted in transit
- Session IDs random generated
- No persistent cookies

### **API Security**
- Rate limiting implemented
- Input validation on all endpoints
- SQL injection prevention
- XSS protection

---

## **🧪 Testing Examples**

### **Basic Chat Test**
```bash
# Test simple conversation
curl -X POST "http://localhost:8080/chat" \
  -F "message=Xin chào, tôi cần tư vấn"

# Test with user tracking
curl -X POST "http://localhost:8080/chat" \
  -F "message=Tôi muốn tìm kính cận" \
  -F "user_id=test_user_123"
```

### **File Upload Test**
```bash
# Single image
curl -X POST "http://localhost:8080/chat" \
  -F "message=Tìm sản phẩm giống trong ảnh này" \
  -F "files=@test_product.jpg" \
  -F "user_id=test_user_123"

# Multiple files
curl -X POST "http://localhost:8080/chat" \
  -F "message=So sánh các sản phẩm này" \
  -F "files=@product1.jpg" \
  -F "files=@product2.jpg" \
  -F "files=@specs.pdf"
```

### **Session Management Test**
```bash
# Create new session
SESSION_ID=$(curl -s -X POST "http://localhost:8080/sessions/create" | jq -r '.session_id')

# Chat with specific session
curl -X POST "http://localhost:8080/chat" \
  -F "message=Hello session test" \
  -F "session_id=$SESSION_ID" \
  -F "user_id=test_user"

# Get chat history
curl "http://localhost:8080/sessions/$SESSION_ID/history?user_id=test_user"

# Clear history
curl -X DELETE "http://localhost:8080/sessions/$SESSION_ID/history?user_id=test_user"
```

### **Product Purchase Flow Test**
```bash
# Step 1: Search for products
curl -X POST "http://localhost:8080/chat" \
  -F "message=Tìm kính cận cho nam giới" \
  -F "user_id=test_buyer" \
  -F "session_id=test_session_buy"

# Step 2: Purchase (system auto-extracts product ID)
curl -X POST "http://localhost:8080/chat" \
  -F "message=Tôi muốn mua sản phẩm đó" \
  -F "user_id=test_buyer" \
  -F "session_id=test_session_buy"
```

---

## **📞 Support & Contact**

- **Documentation**: Xem API docs tại `/docs` endpoint
- **Issues**: Report qua GitHub issues
- **Email**: support@eyevi-agent.com
- **Version**: v1.0.0
- **Last Updated**: 2024-01-15

---

*Tài liệu này được cập nhật thường xuyên. Vui lòng check version mới nhất.*