# A2A Search Agent - Tìm kiếm sản phẩm mắt kính CLIP

Agent tìm kiếm sản phẩm mắt kính tiên tiến với khả năng A2A (Agent-to-Agent) communication, sử dụng công nghệ CLIP multimodal để tìm kiếm bằng văn bản, hình ảnh và kết hợp đa phương thức.

## 🚀 Tính năng chính

### Khả năng tìm kiếm
- **Tìm kiếm văn bản**: Tìm kiếm sản phẩm dựa trên mô tả bằng tiếng Việt/Anh
- **Tìm kiếm hình ảnh**: Upload ảnh để tìm sản phẩm tương tự  
- **Tìm kiếm đa phương thức**: Kết hợp văn bản + hình ảnh
- **Tìm kiếm cá nhân hóa**: Dựa trên phân tích khuôn mặt và sở thích
- **A2A Protocol**: Hỗ trợ giao tiếp agent-to-agent đầy đủ
- **CLIP Technology**: Sử dụng mô hình CLIP hiện đại cho độ chính xác cao

### Tính năng kỹ thuật
- **CLIP Multimodal**: OpenAI CLIP với khả năng fine-tuning
- **Qdrant Vector DB**: Vector database hiệu suất cao
- **Async Processing**: Xử lý bất đồng bộ với timeout protection
- **Custom Model Support**: Hỗ trợ mô hình CLIP đã fine-tune
- **A2A SDK**: Giao tiếp với các agent khác

## 📋 Yêu cầu hệ thống

- Python 3.8+
- Google Gemini API key
- Qdrant vector database (đã có dữ liệu sản phẩm)
- A2A SDK
- PyTorch + Transformers
- CLIP model weights

## 🛠️ Cài đặt

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình môi trường

Tạo file `.env`:

```env
GOOGLE_API_KEY=your_google_api_key_here
QDRANT_HOST=localhost
QDRANT_PORT=6333
CLIP_MODEL_PATH=./models/clip/CLIP_FTMT.pt
```

### 3. Chuẩn bị Qdrant và dữ liệu

```bash
# Khởi động Qdrant
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_data:/qdrant/storage \
    qdrant/qdrant

# Kiểm tra Qdrant health
curl http://localhost:6333/health
```

### 4. Kiểm tra CLIP model

```bash
# Đảm bảo CLIP model được tải đúng
python -c "from transformers import CLIPModel; print('CLIP OK')"
```

## 🏃‍♂️ Chạy Search Agent

### Khởi động A2A Server

```bash
# Cách 1: Chạy A2A server (integrated mode)
python run_server.py --a2a

# Cách 2: Với host và port tùy chỉnh (A2A mode)
python run_server.py --host 0.0.0.0 --port 10002 --a2a

# Cách 3: Chạy FastAPI server (traditional mode)
python run_server.py --host 0.0.0.0 --port 8001

# Cách 4: Bỏ qua kiểm tra prerequisites
python run_server.py --a2a --skip-checks
```

**Lưu ý**: Server mặc định chạy trên `localhost:10002`

### Endpoints

- **Agent Card**: `http://localhost:10002/.well-known/agent.json`
- **A2A Endpoint**: `http://localhost:10002/`
- **Health Check**: Sử dụng agent card để kiểm tra

## 🧪 Testing

### Client A2A

```bash
# Demo tìm kiếm văn bản
python a2a_client.py demo

# Demo tìm kiếm hình ảnh
python a2a_client.py image

# Chế độ chat tương tác
python a2a_client.py chat

# Tìm kiếm một câu truy vấn
python a2a_client.py "Tìm kính cận thị màu đen cho nam"
```

### Từ Agent khác

```python
from a2a.client import A2AClient
from a2a.types import SendMessageRequest

# Kết nối đến Search Agent
client = A2AClient("http://localhost:10002")

# Tìm kiếm bằng văn bản
request = SendMessageRequest(
    message="Kính râm thể thao màu đen",
    stream=False
)

task = await client.send_message(request)
result = await client.wait_for_completion(task.id)
print(result)
```

## 🛠️ Kỹ năng có sẵn

### 1. Tìm kiếm bằng văn bản (text_search)
Tìm kiếm sản phẩm dựa trên mô tả văn bản
- **Examples**: 
  - "Tìm kính cận thị cho nam"
  - "Kính râm thể thao màu đen"
  - "Gọng vuông titan cho khuôn mặt tròn"

### 2. Tìm kiếm bằng hình ảnh (image_search)
Tìm kiếm sản phẩm tương tự từ hình ảnh
- **Examples**:
  - "Upload ảnh kính để tìm sản phẩm tương tự"
  - "Tìm kính giống với hình ảnh đã có"

### 3. Tìm kiếm đa phương thức (multimodal_search)
Kết hợp văn bản và hình ảnh
- **Examples**:
  - "Tìm kính màu đỏ + upload ảnh mẫu"
  - "Gọng kim loại như trong ảnh nhưng màu khác"

### 4. Tìm kiếm cá nhân hóa (personalized_search)
Tìm kiếm phù hợp với khuôn mặt và sở thích
- **Examples**:
  - "Gợi ý kính phù hợp với khuôn mặt tròn"
  - "Tìm kính theo phong cách thời trang hiện đại"

## 💬 Ví dụ tìm kiếm

### Tìm kiếm văn bản
```
User: "Tìm kính cận thị cho nam màu đen"
Agent: 🎯 Tìm thấy 12 sản phẩm phù hợp:
       
       1. **Kính cận thị Ray-Ban RB5228**
          🏷️ Thương hiệu: Ray-Ban
          💰 Giá: 2,500,000 VNĐ
          📝 Mô tả: Gọng nhựa màu đen, thiết kế classic...
          ⭐ Độ phù hợp: 0.92
       
       2. **Gọng titan Oakley OX3164**
          🏷️ Thương hiệu: Oakley
          💰 Giá: 3,200,000 VNĐ
          ...
```

### Tìm kiếm hình ảnh
```
User: [Upload ảnh kính] "Tìm sản phẩm tương tự"
Agent: 🖼️ Phân tích hình ảnh thành công!
       🎯 Tìm thấy 8 sản phẩm tương tự:
       
       📋 Tóm tắt tìm kiếm:
       Đã phát hiện: Gọng vuông, màu nâu, chất liệu acetate
       
       1. **Persol PO3007V**
          🏷️ Tương tự 94%
          📝 Gọng acetate vuông, màu havana
          ...
```

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   A2A Client    │───▶│  A2A Server     │───▶│  SearchAgent    │
│  (Other Agent)  │    │(run_server.py)  │    │   (CLIP-based)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │SearchExecutor   │    │ ProductSearch   │
                       │ (A2A Bridge)    │    │ (CLIP Service)  │
                       └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                               ┌─────────────────┐
                                               │ Qdrant Vector   │
                                               │ Database        │
                                               │ (Products)      │
                                               └─────────────────┘
```

## 🔧 Cấu hình nâng cao

### Tùy chỉnh Agent Card

```python
# Trong run_server.py (function create_a2a_server), thêm skill mới
additional_skill = AgentSkill(
    id='color_search',
    name='Tìm kiếm theo màu sắc',
    description='Tìm sản phẩm theo màu sắc cụ thể',
    examples=['Tìm kính màu xanh navy', 'Gọng màu hồng cho nữ']
)

search_skills.append(additional_skill)
```

### Tùy chỉnh CLIP Parameters

```python
# Trong SearchAgent.__init__()
custom_model_path = "path/to/your/fine_tuned_clip.pt"
default_limit = 10  # Số sản phẩm trả về
cache_size = 200   # Cache size cho tối ưu hiệu suất
```

### Cấu hình Qdrant

```python
# Environment variables
QDRANT_HOST=your_qdrant_host
QDRANT_PORT=6333
QDRANT_COLLECTION=eyewear_products
```

## 🐛 Khắc phục sự cố

### Lỗi thường gặp

#### 1. "GOOGLE_API_KEY not found"
```bash
# Kiểm tra .env file
cat .env | grep GOOGLE_API_KEY

# Hoặc set trực tiếp
export GOOGLE_API_KEY="your_key_here"
```

#### 2. "Cannot connect to Qdrant"
```bash
# Khởi động Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Kiểm tra connection
curl http://localhost:6333/health
```

#### 3. "CLIP model loading failed"
```bash
# Kiểm tra CLIP dependencies
pip install torch transformers

# Test CLIP import
python -c "from transformers import CLIPModel, CLIPProcessor; print('OK')"
```

#### 4. "No products found"
```bash
# Kiểm tra Qdrant có collection không
curl http://localhost:6333/collections

# Kiểm tra collection có data không
curl http://localhost:6333/collections/eyewear_products
```

### Performance Tuning

```python
# Tối ưu cache
@lru_cache(maxsize=500)
def search_cache(query):
    pass

# Batch processing cho nhiều queries
async def batch_search(queries):
    tasks = [search_agent.search(q) for q in queries]
    return await asyncio.gather(*tasks)
```

## 📈 Hiệu suất

- **Response Time**: 2-5 giây (tùy số lượng sản phẩm)
- **CLIP Encoding**: < 1 giây cho text/image
- **Qdrant Search**: < 500ms 
- **Concurrent Requests**: Hỗ trợ multiple requests đồng thời
- **Memory Usage**: ~2GB với CLIP model loaded

## 🔒 Bảo mật

- Environment variables cho sensitive data
- Request validation và image size limits
- Error handling để tránh model information leakage
- Timeout protection cho CLIP operations

## 📚 Tích hợp với Agent khác

### Ví dụ: Advisor Agent gọi Search Agent

```python
# Trong Advisor Agent
from a2a.client import A2AClient

async def find_recommended_products(user_needs):
    search_client = A2AClient("http://localhost:10002")
    
    # Tạo search query từ recommendation
    query = f"Tìm {user_needs['frame_type']} màu {user_needs['color']} cho {user_needs['face_shape']}"
    
    request = SendMessageRequest(message=query, stream=False)
    task = await search_client.send_message(request)
    products = await search_client.wait_for_completion(task.id)
    
    return products
```

### Workflow đa Agent

```python
# Example: Quy trình tư vấn + tìm kiếm + đặt hàng
async def complete_consultation_flow(user_query, user_image=None):
    # 1. Advisor Agent phân tích nhu cầu
    advisor_analysis = await advisor_agent.analyze_needs(user_query)
    
    # 2. Search Agent tìm sản phẩm phù hợp
    search_params = advisor_analysis.search_criteria
    if user_image:
        search_params["image_data"] = user_image
    
    products = await search_agent.find_products(search_params)
    
    # 3. Order Agent chuẩn bị đặt hàng
    order_options = await order_agent.prepare_order(products.top_products)
    
    return {
        "consultation": advisor_analysis,
        "recommended_products": products,
        "order_options": order_options
    }
```

## 📝 API Reference

### Search Query Formats

#### Text Search
```
"Tìm kính cận thị màu đen cho nam"
```

#### Image Search  
```
"data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEA..."
```

#### Multimodal Search
```
"Tìm gọng tương tự màu khác data:image/jpeg;base64,..."
```

#### Personalized Search
```
"Gợi ý kính phù hợp {"face_shape": "round", "age": 25, "style": "modern"}"
```

### Response Format

```json
{
  "products": [
    {
      "id": "PROD001",
      "name": "Ray-Ban RB5228",
      "brand": "Ray-Ban", 
      "price": "2,500,000 VNĐ",
      "description": "Gọng nhựa màu đen...",
      "score": 0.92,
      "category": "Cận thị",
      "image_url": "https://...",
      "features": ["UV Protection", "Anti-glare"]
    }
  ],
  "count": 12,
  "summary": "Tìm thấy 12 sản phẩm kính cận thị phù hợp...",
  "query_info": {
    "type": "text_search",
    "processing_time": 2.1,
    "model_used": "clip-vit-base-patch32"
  }
}
```

### Health Check Response

```json
{
  "agent_type": "search_clip",
  "status": "healthy", 
  "search_agent_available": true,
  "active_tasks": 0,
  "search_functionality": "working",
  "qdrant_status": "connected",
  "clip_model_status": "loaded",
  "last_search": "2024-01-15T10:30:00Z"
}
```

## 🚨 Limitations

- **Image Size**: Tối đa 10MB per image
- **Batch Search**: Tối đa 10 queries per request
- **Rate Limiting**: 100 requests/minute per client
- **Language**: Chủ yếu Vietnamese + English
- **Products**: Chỉ hoạt động với dữ liệu đã được index

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
- Test với `python a2a_client.py chat`
- Email: support@yourcompany.com

---

**🚀 Built with A2A Protocol, CLIP Multimodal, Qdrant & PyTorch**

*AI Search Agent - Tìm kiếm thông minh với công nghệ hiện đại!* 🔍✨ 