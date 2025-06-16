# Thiết kế hệ thống Search Agent

## 1. Tổng quan

Search Agent là một trong những agent chuyên biệt trong hệ thống đa agent (multi-agent) của ứng dụng gợi ý kính mắt EyeVi. Agent này có khả năng tìm kiếm sản phẩm kính mắt dựa trên văn bản, hình ảnh, hoặc kết hợp cả hai, đồng thời tích hợp với kết quả phân tích khuôn mặt để đưa ra gợi ý phù hợp.

## 2. Công nghệ sử dụng

### 2.1. Framework và thư viện chính

- **LangChain**: Framework xây dựng chuỗi xử lý của agent
- **LangGraph**: Framework xây dựng luồng công việc dạng đồ thị cho agent
- **FastAPI**: Framework phát triển API RESTful
- **Qdrant**: Vector database lưu trữ embedding sản phẩm kính mắt
- **Transformers (Hugging Face)**: Thư viện cho các mô hình NLP và Computer Vision

### 2.2. Mô hình AI

- **CLIP (Contrastive Language-Image Pre-training)**: Mô hình đa phương thức (multimodal) của OpenAI để xử lý cả văn bản và hình ảnh
- **Google Gemini**: Mô hình ngôn ngữ lớn (LLM) từ Google để phân loại ý định và trích xuất thuộc tính

### 2.3. Giao thức

- **A2A (Agent-to-Agent)**: Giao thức cho phép các agent giao tiếp với nhau
- **JSON-RPC**: Giao thức gọi thủ tục từ xa sử dụng JSON

## 3. Kiến trúc hệ thống

### 3.1. Kiến trúc tổng thể

Search Agent được xây dựng theo kiến trúc đồ thị có trạng thái (StateGraph), trong đó mỗi node đại diện cho một bước xử lý trong quy trình tìm kiếm. Kiến trúc này cho phép:

- **Tính module hóa**: Mỗi node có thể được phát triển, thay thế hoặc cải tiến độc lập
- **Định tuyến linh hoạt**: Luồng xử lý có thể thay đổi dựa trên kết quả của các node trước đó
- **Dễ dàng mở rộng**: Thêm các node mới để hỗ trợ các chức năng tìm kiếm bổ sung

### 3.2. Các thành phần chính

1. **Agent Interface**: Giao diện tương tác với các agent khác thông qua giao thức A2A
2. **Search Chain**: Chuỗi xử lý chính của agent, quản lý luồng công việc
3. **Node System**: Các node xử lý chuyên biệt trong đồ thị
4. **Vector Database Client**: Kết nối với Qdrant để thực hiện tìm kiếm ngữ nghĩa
5. **API Layer**: Cung cấp các endpoint RESTful để tương tác với agent

## 4. Workflow và luồng xử lý

### 4.1. Sơ đồ workflow tổng quát

```
[Input] → [Intent Classifier] → [Intent Router] → [Attribute Extractor] → [Embed Query] → [Semantic Search] → [Format Response] → [Output]
```

### 4.2. Các trạng thái (State) trong workflow

Search Agent sử dụng một đối tượng `SearchState` để lưu trữ và truyền thông tin giữa các node. Các trường chính trong state bao gồm:

- `query`: Câu truy vấn tìm kiếm ban đầu
- `image_data`: Dữ liệu hình ảnh (nếu có)
- `analysis_result`: Kết quả phân tích khuôn mặt (nếu có)
- `intent`: Ý định được phân loại
- `extracted_attributes`: Các thuộc tính được trích xuất từ query
- `normalized_query`: Câu truy vấn đã được chuẩn hóa
- `search_type`: Loại tìm kiếm (text, image, combined)
- `text_embedding`: Vector embedding của văn bản
- `image_embedding`: Vector embedding của hình ảnh
- `search_results`: Kết quả tìm kiếm từ Qdrant
- `final_response`: Kết quả cuối cùng được định dạng
- `error`: Thông tin lỗi (nếu có)

## 5. Chi tiết các node trong đồ thị

### 5.1. Intent Classifier Node

**Chức năng**: Phân loại ý định của người dùng từ câu truy vấn.

**Input**: `query` (câu truy vấn)

**Output**: `intent` (ý định được phân loại)

**Công nghệ**: Google Gemini LLM

**Các intent hỗ trợ**:
- `search_product`: Tìm kiếm sản phẩm
- `product_detail`: Xem chi tiết sản phẩm
- `compare_products`: So sánh sản phẩm
- `filter_by_feature`: Lọc theo tính năng
- `faq_about_material`: Hỏi về vật liệu
- `availability_check`: Kiểm tra tình trạng sẵn có
- `recommendation_request`: Yêu cầu đề xuất
- `product_category_stats`: Thống kê danh mục sản phẩm
- `unknown`: Không xác định

### 5.2. Intent Router Node

**Chức năng**: Định tuyến luồng xử lý dựa trên intent.

**Input**: `intent` (ý định đã phân loại)

**Output**: Tên của node tiếp theo

**Xử lý**:
- Nếu intent là `search_product`: → Attribute Extractor
- Nếu intent là `product_detail`: → Attribute Extractor (tạm thời)
- Nếu intent là `compare_products`: → Attribute Extractor (tạm thời)
- Các intent khác: → Attribute Extractor (mặc định)

### 5.3. Attribute Extractor Node

**Chức năng**: Trích xuất các thuộc tính từ câu truy vấn.

**Input**: `query` (câu truy vấn)

**Output**:
- `extracted_attributes`: Các thuộc tính được trích xuất
- `normalized_query`: Câu truy vấn đã được chuẩn hóa

**Công nghệ**: Google Gemini LLM

**Các thuộc tính trích xuất**:
- `category`: Loại sản phẩm (Kính Mát, Gọng Kính)
- `gender`: Giới tính (Nam, Nữ, Unisex)
- `brand`: Thương hiệu
- `color`: Màu sắc
- `frameMaterial`: Vật liệu khung
- `frameShape`: Hình dạng khung

### 5.4. Embed Query Node

**Chức năng**: Chuyển đổi query thành vector embedding.

**Input**:
- `normalized_query`: Câu truy vấn đã chuẩn hóa
- `image_data`: Dữ liệu hình ảnh (nếu có)

**Output**:
- `search_type`: Loại tìm kiếm (text, image, combined)
- `text_embedding`: Vector embedding của văn bản
- `image_embedding`: Vector embedding của hình ảnh

**Công nghệ**: CLIP (Contrastive Language-Image Pre-training)

### 5.5. Semantic Search Node

**Chức năng**: Thực hiện tìm kiếm ngữ nghĩa trên Qdrant.

**Input**:
- `search_type`: Loại tìm kiếm
- `text_embedding`: Vector embedding của văn bản
- `image_embedding`: Vector embedding của hình ảnh
- `extracted_attributes`: Các thuộc tính để lọc

**Output**: `search_results`: Danh sách kết quả tìm kiếm

**Công nghệ**: Qdrant Vector Database

**Các phương thức tìm kiếm**:
- Tìm kiếm bằng text
- Tìm kiếm bằng hình ảnh
- Tìm kiếm kết hợp (text + hình ảnh)

### 5.6. Format Response Node

**Chức năng**: Định dạng kết quả tìm kiếm thành phản hồi cuối cùng.

**Input**:
- `search_results`: Kết quả tìm kiếm
- `query`: Câu truy vấn ban đầu
- `normalized_query`: Câu truy vấn đã chuẩn hóa
- `extracted_attributes`: Các thuộc tính đã trích xuất

**Output**: `final_response`: Kết quả cuối cùng được định dạng

## 6. Sơ đồ luồng xử lý chi tiết

### 6.1. Luồng xử lý tìm kiếm bằng văn bản

```
[Văn bản đầu vào]
      ↓
[Intent Classifier] → Phân loại ý định (search_product)
      ↓
[Intent Router] → Định tuyến đến Attribute Extractor
      ↓
[Attribute Extractor] → Trích xuất category, brand, color, frameShape...
      ↓
[Embed Query] → Chuyển văn bản thành vector embedding
      ↓
[Semantic Search] → Tìm kiếm sản phẩm tương tự trong Qdrant
      ↓
[Format Response] → Định dạng kết quả thành JSON
      ↓
[Kết quả tìm kiếm]
```

### 6.2. Luồng xử lý tìm kiếm bằng hình ảnh

```
[Hình ảnh đầu vào]
      ↓
[Intent Classifier] → Bỏ qua (không có văn bản)
      ↓
[Intent Router] → Định tuyến đến Attribute Extractor
      ↓
[Attribute Extractor] → Không có thuộc tính để trích xuất
      ↓
[Embed Query] → Chuyển hình ảnh thành vector embedding
      ↓
[Semantic Search] → Tìm kiếm sản phẩm tương tự trong Qdrant
      ↓
[Format Response] → Định dạng kết quả thành JSON
      ↓
[Kết quả tìm kiếm]
```

### 6.3. Luồng xử lý tìm kiếm kết hợp (văn bản + hình ảnh)

```
[Văn bản + Hình ảnh đầu vào]
      ↓
[Intent Classifier] → Phân loại ý định (search_product)
      ↓
[Intent Router] → Định tuyến đến Attribute Extractor
      ↓
[Attribute Extractor] → Trích xuất thuộc tính từ văn bản
      ↓
[Embed Query] → Chuyển văn bản và hình ảnh thành vector embedding
      ↓
[Semantic Search] → Tìm kiếm kết hợp trong Qdrant (w_text=0.6, w_image=0.4)
      ↓
[Format Response] → Định dạng kết quả thành JSON
      ↓
[Kết quả tìm kiếm]
```

### 6.4. Luồng xử lý tìm kiếm với phân tích khuôn mặt

```
[Văn bản + Kết quả phân tích khuôn mặt]
      ↓
[Intent Classifier] → Phân loại ý định (search_product)
      ↓
[Intent Router] → Định tuyến đến Attribute Extractor
      ↓
[Attribute Extractor] → Trích xuất thuộc tính từ văn bản
      ↓
[Embed Query] → Chuyển văn bản thành vector embedding
      ↓
[Semantic Search] → Tìm kiếm trong Qdrant + lọc theo recommended_shapes
      ↓
[Format Response] → Định dạng kết quả thành JSON + thêm recommended_shapes
      ↓
[Kết quả tìm kiếm với đề xuất dựa trên khuôn mặt]
```

## 7. API Endpoints

### 7.1. Endpoint chính

- **POST /search**: Tìm kiếm sản phẩm với văn bản và/hoặc hình ảnh
- **POST /search/text**: Tìm kiếm sản phẩm chỉ với văn bản
- **GET /**: Kiểm tra trạng thái của agent

### 7.2. A2A Endpoints

- **POST /.well-known/agent.json**: Trả về Agent Card với thông tin về agent
- **POST /**: Xử lý các yêu cầu JSON-RPC từ Host Agent

## 8. Tương lai phát triển

- Thêm các intent chuyên biệt (product_detail, compare_products)
- Cải thiện khả năng lọc sản phẩm theo giá
- Thêm tìm kiếm theo thương hiệu ưa thích
- Lưu trữ lịch sử tìm kiếm của người dùng
- Tối ưu cache để giảm thời gian tìm kiếm
- Sử dụng batch processing cho các truy vấn phổ biến
- Tích hợp với Milvus để so sánh với Qdrant
