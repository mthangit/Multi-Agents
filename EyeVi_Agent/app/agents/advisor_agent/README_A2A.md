# A2A Advisor Agent - Chuyên gia tư vấn mắt kính

Agent tư vấn chuyên sâu về mắt kính và quang học với khả năng A2A (Agent-to-Agent) communication, sử dụng cơ sở dữ liệu RAG để đưa ra lời khuyên chính xác và chuyên nghiệp.

## 🚀 Tính năng chính

### Khả năng tư vấn
- **Tư vấn y tế**: Hỗ trợ các vấn đề về tật khúc xạ (cận thị, viễn thị, loạn thị, lão thị)
- **Gợi ý sản phẩm**: Đề xuất loại tròng kính và gọng phù hợp
- **Tư vấn kỹ thuật**: Giải thích các khía cạnh kỹ thuật về quang học
- **Tư vấn phong cách**: Hướng dẫn chọn kiểu dáng phù hợp với khuôn mặt
- **A2A Protocol**: Hỗ trợ giao tiếp agent-to-agent đầy đủ
- **RAG Database**: Tìm kiếm thông tin từ cơ sở dữ liệu chuyên ngành

### Tính năng kỹ thuật
- **LangChain & RAG**: Sử dụng Retrieval-Augmented Generation
- **Google Gemini**: Tích hợp LLM tiên tiến
- **Qdrant Vector DB**: Tìm kiếm semantic hiệu quả
- **A2A SDK**: Giao tiếp với các agent khác
- **Async Processing**: Xử lý bất đồng bộ hiệu suất cao

## 📋 Yêu cầu hệ thống

- Python 3.8+
- Google Gemini API key
- Qdrant vector database
- A2A SDK
- Cơ sở dữ liệu PDF đã được ingest

## 🛠️ Cài đặt

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình môi trường

Tạo file `.env`:

```env
GOOGLE_API_KEY=your_google_api_key_here
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_key_if_needed
COLLECTION_NAME=eyewear_knowledge
```

### 3. Chuẩn bị dữ liệu

```bash
# Đặt file PDF vào thư mục data/
mkdir data
cp your_eyewear_documents.pdf data/

# Chạy data ingestion
python ingest_data.py
```

### 4. Kiểm tra Qdrant

```bash
# Đảm bảo Qdrant đang chạy
docker run -p 6333:6333 qdrant/qdrant
```

## 🏃‍♂️ Chạy Advisor Agent

### Khởi động A2A Server

```bash
# Cách 1: Khởi động cơ bản
python a2a_main.py

# Cách 2: Với tùy chọn
python a2a_main.py --host 0.0.0.0 --port 10001

# Cách 3: Bỏ qua kiểm tra prerequisites
python a2a_main.py --skip-checks
```

**Lưu ý**: Server mặc định chạy trên `localhost:10001`

### Endpoints

- **Agent Card**: `http://localhost:10001/.well-known/agent.json`
- **A2A Endpoint**: `http://localhost:10001/`
- **Health Check**: Sử dụng agent card để kiểm tra

## 🧪 Testing

### Client A2A

```bash
# Demo tự động với các câu hỏi mẫu
python a2a_client.py demo

# Chế độ chat tương tác
python a2a_client.py chat

# Gửi một câu hỏi
python a2a_client.py "Tôi bị cận thị 3 độ, nên chọn tròng kính nào?"
```

### Từ Agent khác

```python
from a2a.client import A2AClient
from a2a.types import SendMessageRequest

# Kết nối đến Advisor Agent
client = A2AClient("http://localhost:10001")

# Gửi yêu cầu tư vấn
request = SendMessageRequest(
    message="Kính chống ánh sáng xanh có hiệu quả không?",
    stream=False
)

task = await client.send_message(request)
result = await client.wait_for_completion(task.id)
print(result)
```

## 🛠️ Kỹ năng có sẵn

### 1. Tư vấn mắt kính (eyewear_consultation)
Tư vấn chuyên sâu dựa trên kiến thức chuyên ngành
- **Examples**: 
  - "Tôi bị cận thị 2.5 độ, nên chọn loại tròng kính nào?"
  - "Kính chống ánh sáng xanh có thực sự hiệu quả không?"

### 2. Gợi ý sản phẩm (product_recommendation)
Đề xuất sản phẩm phù hợp với nhu cầu cụ thể
- **Examples**:
  - "Tôi làm việc nhiều với máy tính, cần loại kính nào?"
  - "Gọng titan có ưu điểm gì so với gọng nhựa?"

### 3. Tư vấn kỹ thuật (technical_advice)
Giải thích các khía cạnh kỹ thuật
- **Examples**:
  - "Chỉ số khúc xạ của tròng kính ảnh hưởng như thế nào?"
  - "Lớp phủ chống phản xạ hoạt động ra sao?"

### 4. Tư vấn phong cách (style_consultation)
Hướng dẫn về kiểu dáng và thời trang
- **Examples**:
  - "Khuôn mặt vuông nên chọn gọng như thế nào?"
  - "Xu hướng kính mắt năm 2024 là gì?"

## 💬 Ví dụ hội thoại

### Tư vấn y tế
```
User: "Tôi bị cận thị 3 độ và hay nhức đầu khi đọc sách"
Agent: Với cận thị 3 độ, bạn cần tròng kính có độ khúc xạ phù hợp. 
       Việc nhức đầu có thể do:
       1. Độ kính không chính xác
       2. Cần kiểm tra loạn thị
       3. Khoảng cách đọc không phù hợp
       
       Tôi khuyên bạn nên...
       ⚠️ Lưu ý: Hãy thăm khám bác sĩ nhãn khoa để được chẩn đoán chính xác.
```

### Tư vấn sản phẩm
```
User: "So sánh tròng kính Crizal và tròng kính thường"
Agent: Tròng kính Crizal là loại có lớp phủ cao cấp với những ưu điểm:
       
       **Crizal:**
       - Chống phản xạ 99%
       - Chống bụi bẩn và nước
       - Độ trong suốt cao hơn
       - Tuổi thọ lâu hơn
       
       **Tròng kính thường:**
       - Giá thành thấp hơn
       - Phù hợp nhu cầu cơ bản
       
       💡 Gợi ý: Nếu bạn thường xuyên sử dụng máy tính hoặc lái xe ban đêm, 
       Crizal sẽ mang lại trải nghiệm tốt hơn đáng kể.
```

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   A2A Client    │───▶│  A2A Server     │───▶│   PDFChatbot    │
│  (Other Agent)  │    │ (a2a_main.py)   │    │  (RAG-based)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │AdvisorExecutor  │    │  Qdrant Vector  │
                       │ (A2A Bridge)    │    │    Database     │
                       └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                               ┌─────────────────┐
                                               │ Knowledge Base  │
                                               │ (PDF Documents) │
                                               └─────────────────┘
```

## 🔧 Cấu hình nâng cao

### Tùy chỉnh Agent Card

```python
# Trong a2a_main.py, tùy chỉnh skills
additional_skill = AgentSkill(
    id='custom_skill',
    name='Tư vấn đặc biệt',
    description='Mô tả kỹ năng mới',
    examples=['Ví dụ 1', 'Ví dụ 2']
)

advisor_skills.append(additional_skill)
```

### Tùy chỉnh RAG Parameters

```python
# Trong config.py
TOP_K_DOCUMENTS = 5  # Số documents retrieve
SIMILARITY_THRESHOLD = 0.7  # Ngưỡng similarity
GEMINI_TEMPERATURE = 0.3  # Độ creative của AI
```

## 🐛 Khắc phục sự cố

### Lỗi thường gặp

#### 1. "GOOGLE_API_KEY not found"
```bash
# Kiểm tra file .env
cat .env | grep GOOGLE_API_KEY

# Hoặc set trực tiếp
export GOOGLE_API_KEY="your_key_here"
```

#### 2. "Data directory not found"
```bash
# Tạo thư mục và chạy ingestion
mkdir data
cp your_pdfs.pdf data/
python ingest_data.py
```

#### 3. "Qdrant connection failed"
```bash
# Khởi động Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Hoặc kiểm tra URL trong .env
```

#### 4. "Agent không phản hồi"
```bash
# Kiểm tra log server
python a2a_main.py --skip-checks

# Kiểm tra port có bị chiếm
lsof -i :10001
```

### Logs và Debug

Agent cung cấp logging chi tiết:
- Startup information
- Request processing
- RAG query details  
- Error messages với stack trace

## 📈 Hiệu suất

- **Response Time**: 3-8 giây (tùy độ phức tạp câu hỏi)
- **RAG Retrieval**: < 1 giây
- **Concurrent Requests**: Hỗ trợ multiple requests đồng thời
- **Memory Usage**: Tối ưu cho vector database lớn

## 🔒 Bảo mật

- Environment variables cho sensitive data
- Request validation và sanitization
- Error handling để tránh information leakage
- Timeout protection cho async operations

## 📚 Tích hợp với Agent khác

### Ví dụ: Order Agent gọi Advisor Agent

```python
# Trong Order Agent
from a2a.client import A2AClient

async def get_product_advice(product_query):
    advisor_client = A2AClient("http://localhost:10001")
    
    request = SendMessageRequest(
        message=f"Tư vấn về sản phẩm: {product_query}",
        stream=False
    )
    
    task = await advisor_client.send_message(request)
    advice = await advisor_client.wait_for_completion(task.id)
    
    return advice
```

### Workflow đa Agent

```python
# Example: Quy trình tư vấn tổng hợp
async def comprehensive_consultation(user_query):
    # 1. Advisor Agent phân tích nhu cầu
    advisor_analysis = await advisor_agent.analyze_needs(user_query)
    
    # 2. Search Agent tìm sản phẩm phù hợp
    products = await search_agent.find_products(advisor_analysis.recommendations)
    
    # 3. Order Agent xử lý đặt hàng
    order_options = await order_agent.prepare_order(products)
    
    return {
        "advice": advisor_analysis,
        "products": products,
        "order_options": order_options
    }
```

## 📝 API Reference

### Agent Card Fields

```json
{
  "name": "Advisor Agent - Chuyên gia tư vấn mắt kính",
  "description": "Agent tư vấn chuyên sâu về mắt kính...",
  "version": "1.0.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": true
  },
  "skills": [
    {
      "id": "eyewear_consultation",
      "name": "Tư vấn mắt kính",
      "description": "Tư vấn chuyên sâu về mắt kính...",
      "tags": ["eyewear", "consultation", "optics", "vision"],
      "examples": ["Tôi bị cận thị 2.5 độ..."]
    }
  ]
}
```

### Health Check Response

```json
{
  "agent_type": "advisor_rag",
  "status": "healthy",
  "chatbot_available": true,
  "active_tasks": 0,
  "rag_database_status": "success",
  "chatbot_health": {
    "status": "success",
    "components": {
      "qdrant": "connected",
      "embedding": "ready",
      "llm": "ready"
    }
  }
}
```

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch
3. Implement changes  
4. Test với `python a2a_client.py demo`
5. Tạo pull request

## 📄 License

[Your License Here]

## 🆘 Hỗ trợ

- Kiểm tra troubleshooting section
- Xem logs để debug
- Tạo issue với reproduction steps
- Email: support@yourcompany.com

---

**🚀 Built with A2A Protocol, LangChain RAG, Google Gemini & Qdrant** 

*Chuyên gia tư vấn mắt kính AI - Luôn sẵn sàng hỗ trợ!* 👓✨ 