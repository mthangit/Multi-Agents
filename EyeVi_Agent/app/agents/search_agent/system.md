# Hệ thống Search Agent của EyeVi

## 1. Tổng quan

Search Agent là một hệ thống thông minh được thiết kế để tìm kiếm và gợi ý sản phẩm kính mắt dựa trên đầu vào của người dùng. Hệ thống có khả năng xử lý nhiều loại đầu vào khác nhau:

- Tìm kiếm bằng **văn bản**: Người dùng mô tả sản phẩm họ muốn tìm
- Tìm kiếm bằng **hình ảnh**: Người dùng tải lên hình ảnh của kính mắt
- Tìm kiếm **kết hợp**: Người dùng cung cấp cả văn bản và hình ảnh
- **Tư vấn sản phẩm**: Người dùng yêu cầu tư vấn về loại kính phù hợp

Hệ thống được xây dựng theo kiến trúc đồ thị có trạng thái (StateGraph) từ LangGraph, trong đó mỗi node đại diện cho một bước xử lý trong quy trình tìm kiếm. Kiến trúc này mang lại nhiều lợi ích:

- **Tính module hóa**: Mỗi node có thể được phát triển, thay thế hoặc cải tiến độc lập
- **Định tuyến linh hoạt**: Luồng xử lý có thể thay đổi dựa trên kết quả của các node trước đó
- **Dễ dàng mở rộng**: Thêm các node mới để hỗ trợ các chức năng tìm kiếm bổ sung

## 2. Kiến trúc hệ thống

### 2.1. Mô hình trạng thái (State Model)

Toàn bộ thông tin trong quá trình xử lý được lưu trữ trong một đối tượng `SearchState`, cho phép các node chia sẻ và cập nhật thông tin. Các trường chính trong state bao gồm:

- `query`: Câu truy vấn tìm kiếm ban đầu
- `image_data`: Dữ liệu hình ảnh (nếu có)
- `intent`: Ý định được phân loại từ câu truy vấn
- `extracted_attributes`: Các thuộc tính được trích xuất từ query
- `normalized_query`: Câu truy vấn đã được chuẩn hóa
- `search_type`: Loại tìm kiếm (text, image, combined)
- `text_embedding`: Vector embedding của văn bản
- `image_embedding`: Vector embedding của hình ảnh
- `search_results`: Kết quả tìm kiếm từ Qdrant
- `final_response`: Kết quả cuối cùng được định dạng

### 2.2. Các node chính và vai trò

Hệ thống Search Agent bao gồm 9 node chính, mỗi node đảm nhận một chức năng cụ thể:

1. **Intent Classifier Node** (Độ quan trọng: Cao)
   - **Vai trò**: Xác định ý định của người dùng từ câu truy vấn
   - **Đầu vào**: Câu truy vấn văn bản
   - **Đầu ra**: Ý định được phân loại (search_product, product_detail, compare_products, recommend_product, unknown)
   - **Tại sao quan trọng**: Node này quyết định luồng xử lý tiếp theo, giúp hệ thống hiểu người dùng thực sự muốn gì

2. **Intent Router Node** (Độ quan trọng: Cao)
   - **Vai trò**: Định tuyến luồng xử lý dựa trên ý định và loại input
   - **Đầu vào**: Ý định và loại input (text, image, cả hai)
   - **Đầu ra**: Quyết định node tiếp theo sẽ xử lý
   - **Tại sao quan trọng**: Đây là "bộ não" điều phối của hệ thống, quyết định cách xử lý mỗi yêu cầu

3. **Attribute Extraction Node** (Độ quan trọng: Cao)
   - **Vai trò**: Trích xuất các thuộc tính sản phẩm từ câu truy vấn
   - **Đầu vào**: Câu truy vấn văn bản
   - **Đầu ra**: Các thuộc tính được trích xuất và câu truy vấn chuẩn hóa
   - **Tại sao quan trọng**: Giúp hiểu chi tiết về sản phẩm người dùng đang tìm kiếm

4. **Image Analysis Node** (Độ quan trọng: Cao)
   - **Vai trò**: Phân tích hình ảnh để trích xuất thông tin về kính mắt
   - **Đầu vào**: Dữ liệu hình ảnh
   - **Đầu ra**: Kết quả phân tích hình ảnh, thuộc tính trích xuất từ hình ảnh
   - **Tại sao quan trọng**: Cho phép tìm kiếm dựa trên hình ảnh, mở rộng khả năng tìm kiếm

5. **Query Combiner Node** (Độ quan trọng: Trung bình)
   - **Vai trò**: Kết hợp thông tin từ phân tích văn bản và hình ảnh
   - **Đầu vào**: Kết quả từ Attribute Extractor và Image Analyzer
   - **Đầu ra**: Query và thuộc tính kết hợp
   - **Tại sao quan trọng**: Tối ưu hóa tìm kiếm khi có cả văn bản và hình ảnh

6. **Embed Query Node** (Độ quan trọng: Cao)
   - **Vai trò**: Chuyển đổi query thành vector embedding
   - **Đầu vào**: Query chuẩn hóa và/hoặc hình ảnh
   - **Đầu ra**: Vector embedding của văn bản và/hoặc hình ảnh
   - **Tại sao quan trọng**: Tạo ra biểu diễn số học cho việc tìm kiếm ngữ nghĩa

7. **Semantic Search Node** (Độ quan trọng: Rất cao)
   - **Vai trò**: Thực hiện tìm kiếm ngữ nghĩa trên Qdrant
   - **Đầu vào**: Vector embedding và các thuộc tính lọc
   - **Đầu ra**: Danh sách kết quả tìm kiếm
   - **Tại sao quan trọng**: Đây là "trái tim" của hệ thống tìm kiếm, trả về sản phẩm phù hợp nhất

8. **Format Response Node** (Độ quan trọng: Cao)
   - **Vai trò**: Định dạng kết quả tìm kiếm thành phản hồi thân thiện
   - **Đầu vào**: Kết quả tìm kiếm, query gốc, thông tin phân tích
   - **Đầu ra**: Phản hồi cuối cùng cho người dùng
   - **Tại sao quan trọng**: Tạo trải nghiệm người dùng tốt qua phản hồi dễ hiểu

9. **Recommendation Node** (Độ quan trọng: Trung bình)
   - **Vai trò**: Đưa ra tư vấn về sản phẩm kính mắt phù hợp
   - **Đầu vào**: Yêu cầu tư vấn của người dùng
   - **Đầu ra**: Lời khuyên về sản phẩm phù hợp
   - **Tại sao quan trọng**: Cung cấp trải nghiệm cá nhân hóa cho người dùng

## 3. Cấu trúc đồ thị và luồng xử lý

### 3.1. Cấu trúc đồ thị tổng quát

Đồ thị của Search Agent có thể được minh họa như sau:

```
                                   ┌───────────────────┐
                                   │                   │
                                   │ Recommendation    │
                                   │ Node              │
                                   │                   │
                                   └───────────────────┘
                                          ▲
                                          │
                                          │ (recommend_product)
                                          │
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│               │    │               │    │               │
│ Intent        │───>│ Intent        │───>│ Attribute     │
│ Classifier    │    │ Router        │    │ Extractor     │
│               │    │               │    │               │
└───────────────┘    └───────────────┘    └───────────────┘
                           │                     │
                           │ (image only)        │ (has image)
                           ▼                     ▼
                     ┌───────────────┐    ┌───────────────┐
                     │               │    │               │
                     │ Image         │───>│ Query         │
                     │ Analyzer      │    │ Combiner      │
                     │               │    │               │
                     └───────────────┘    └───────────────┘
                           │                     │
                           │                     │
                           ▼                     ▼
                     ┌───────────────┐    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
                     │               │    │               │    │               │    │               │
                     │ Embed         │───>│ Semantic      │───>│ Format        │───>│ END           │
                     │ Query         │    │ Search        │    │ Response      │    │               │
                     │               │    │               │    │               │    │               │
                     └───────────────┘    └───────────────┘    └───────────────┘    └───────────────┘
```

Đồ thị này thể hiện các node và các cạnh kết nối giữa chúng. Mỗi cạnh đại diện cho một luồng xử lý có thể xảy ra dựa trên điều kiện cụ thể.

### 3.2. Chi tiết các cạnh và điều kiện

1. **Intent Classifier → Intent Router**
   - **Điều kiện**: Luôn xảy ra
   - **Dữ liệu truyền**: Intent được phân loại

2. **Intent Router → Recommendation Node**
   - **Điều kiện**: Intent là "recommend_product"
   - **Dữ liệu truyền**: Query gốc

3. **Intent Router → Image Analyzer**
   - **Điều kiện**: Chỉ có hình ảnh, không có văn bản
   - **Dữ liệu truyền**: Dữ liệu hình ảnh

4. **Intent Router → Attribute Extractor**
   - **Điều kiện**: Có văn bản hoặc cả văn bản và hình ảnh
   - **Dữ liệu truyền**: Query gốc

5. **Attribute Extractor → Image Analyzer**
   - **Điều kiện**: Có cả văn bản và hình ảnh
   - **Dữ liệu truyền**: Thuộc tính trích xuất từ văn bản, dữ liệu hình ảnh

6. **Image Analyzer → Query Combiner**
   - **Điều kiện**: Có kết quả từ cả Attribute Extractor và Image Analyzer
   - **Dữ liệu truyền**: Thuộc tính trích xuất từ hình ảnh

7. **Image Analyzer → Embed Query**
   - **Điều kiện**: Chỉ có kết quả từ Image Analyzer
   - **Dữ liệu truyền**: Thuộc tính trích xuất từ hình ảnh

8. **Attribute Extractor → Query Combiner**
   - **Điều kiện**: Có cả văn bản và hình ảnh
   - **Dữ liệu truyền**: Thuộc tính trích xuất từ văn bản

9. **Query Combiner → Embed Query**
   - **Điều kiện**: Luôn xảy ra sau Query Combiner
   - **Dữ liệu truyền**: Query và thuộc tính kết hợp

10. **Embed Query → Semantic Search**
    - **Điều kiện**: Luôn xảy ra sau Embed Query
    - **Dữ liệu truyền**: Vector embedding của văn bản và/hoặc hình ảnh

11. **Semantic Search → Format Response**
    - **Điều kiện**: Luôn xảy ra sau Semantic Search
    - **Dữ liệu truyền**: Kết quả tìm kiếm

12. **Format Response → END**
    - **Điều kiện**: Luôn xảy ra sau Format Response
    - **Dữ liệu truyền**: Phản hồi cuối cùng

13. **Recommendation Node → END**
    - **Điều kiện**: Luôn xảy ra sau Recommendation Node
    - **Dữ liệu truyền**: Lời khuyên về sản phẩm

## 4. Chi tiết các luồng xử lý

### 4.1. Luồng xử lý tìm kiếm bằng văn bản

Khi người dùng chỉ nhập văn bản để tìm kiếm, luồng xử lý sẽ như sau:

```
[Văn bản đầu vào] → Intent Classifier → Intent Router → Attribute Extractor → Query Combiner → Embed Query → Semantic Search → Format Response → [Kết quả]
```

**Ví dụ**: Người dùng nhập "Tôi muốn tìm kính mát nam màu đen của RayBan"

1. **Intent Classifier**: 
   - Phân tích câu truy vấn và xác định intent là "search_product"
   - State: `intent = "search_product"`

2. **Intent Router**: 
   - Phát hiện có văn bản, không có hình ảnh
   - Định tuyến đến Attribute Extractor
   - State: `search_type = "text"`

3. **Attribute Extractor**: 
   - Trích xuất thuộc tính: category="Kính Mát", gender="Nam", brand="RAYBAN", color="Đen"
   - Chuẩn hóa query: "Kính Mát Nam RAYBAN màu Đen"
   - State: `extracted_attributes = {...}`, `normalized_query = "Kính Mát Nam RAYBAN màu Đen"`

4. **Query Combiner**: 
   - Không có dữ liệu hình ảnh, giữ nguyên kết quả từ Attribute Extractor
   - State: không thay đổi

5. **Embed Query**: 
   - Chuyển đổi query chuẩn hóa thành vector embedding
   - State: `text_embedding = [...]`

6. **Semantic Search**: 
   - Tìm kiếm sản phẩm dựa trên vector embedding và các thuộc tính lọc
   - Lọc theo category="Kính Mát", gender="Nam", brand="RAYBAN", color="Đen"
   - State: `search_results = [...]`

7. **Format Response**: 
   - Định dạng kết quả tìm kiếm thành phản hồi thân thiện
   - State: `final_response = {...}`

8. **Kết quả**: Trả về danh sách sản phẩm kính mát nam màu đen của RayBan

### 4.2. Luồng xử lý tìm kiếm bằng hình ảnh

Khi người dùng chỉ tải lên hình ảnh để tìm kiếm, luồng xử lý sẽ như sau:

```
[Hình ảnh đầu vào] → Intent Router → Image Analyzer → Embed Query → Semantic Search → Format Response → [Kết quả]
```

**Ví dụ**: Người dùng tải lên hình ảnh một chiếc kính mát

1. **Intent Router**: 
   - Phát hiện chỉ có hình ảnh, không có văn bản
   - Định tuyến đến Image Analyzer
   - State: `search_type = "image"`

2. **Image Analyzer**: 
   - Phân tích hình ảnh và trích xuất thông tin: kính mát màu đen, khung vuông
   - State: `image_analysis = {...}`, `image_extracted_attributes = {...}`

3. **Embed Query**: 
   - Chuyển đổi hình ảnh thành vector embedding
   - State: `image_embedding = [...]`

4. **Semantic Search**: 
   - Tìm kiếm sản phẩm dựa trên vector embedding của hình ảnh
   - Lọc theo các thuộc tính trích xuất từ hình ảnh
   - State: `search_results = [...]`

5. **Format Response**: 
   - Định dạng kết quả tìm kiếm thành phản hồi thân thiện
   - Đưa vào phân tích hình ảnh để giải thích kết quả
   - State: `final_response = {...}`

6. **Kết quả**: Trả về danh sách sản phẩm kính mắt tương tự với hình ảnh

### 4.3. Luồng xử lý tìm kiếm kết hợp (văn bản + hình ảnh)

Khi người dùng cung cấp cả văn bản và hình ảnh, luồng xử lý sẽ như sau:

```
[Văn bản + Hình ảnh] → Intent Classifier → Intent Router → Attribute Extractor → Image Analyzer → Query Combiner → Embed Query → Semantic Search → Format Response → [Kết quả]
```

**Ví dụ**: Người dùng nhập "Tôi muốn tìm kính giống thế này nhưng màu xanh" và tải lên hình ảnh kính mát

1. **Intent Classifier**: 
   - Phân tích câu truy vấn và xác định intent là "search_product"
   - State: `intent = "search_product"`

2. **Intent Router**: 
   - Phát hiện có cả văn bản và hình ảnh
   - Định tuyến đến Attribute Extractor
   - State: `search_type = "combined"`

3. **Attribute Extractor**: 
   - Trích xuất thuộc tính từ văn bản: color="Xanh"
   - State: `text_extracted_attributes = {...}`, `text_normalized_query = "..."`

4. **Image Analyzer**: 
   - Phân tích hình ảnh và trích xuất thông tin: kính mát, khung vuông
   - State: `image_analysis = {...}`, `image_extracted_attributes = {...}`

5. **Query Combiner**: 
   - Kết hợp thông tin từ văn bản và hình ảnh
   - Ưu tiên thuộc tính từ văn bản (màu xanh) thay vì từ hình ảnh
   - State: `extracted_attributes = {...}`, `normalized_query = "..."`

6. **Embed Query**: 
   - Chuyển đổi query và hình ảnh thành vector embedding
   - Kết hợp cả hai vector với trọng số: 60% text, 40% image
   - State: `text_embedding = [...]`, `image_embedding = [...]`

7. **Semantic Search**: 
   - Tìm kiếm sản phẩm dựa trên vector embedding kết hợp
   - Lọc theo các thuộc tính kết hợp, ưu tiên màu xanh
   - State: `search_results = [...]`

8. **Format Response**: 
   - Định dạng kết quả tìm kiếm thành phản hồi thân thiện
   - Giải thích cách kết hợp thông tin từ văn bản và hình ảnh
   - State: `final_response = {...}`

9. **Kết quả**: Trả về danh sách sản phẩm kính mắt tương tự với hình ảnh nhưng màu xanh

### 4.4. Luồng xử lý tư vấn sản phẩm

Khi người dùng yêu cầu tư vấn sản phẩm, luồng xử lý sẽ như sau:

```
[Văn bản đầu vào] → Intent Classifier → Intent Router → Recommendation Node → [Kết quả]
```

**Ví dụ**: Người dùng nhập "Tôi có khuôn mặt tròn, nên đeo kính gì?"

1. **Intent Classifier**: 
   - Phân tích câu truy vấn và xác định intent là "recommend_product"
   - State: `intent = "recommend_product"`

2. **Intent Router**: 
   - Phát hiện intent là "recommend_product"
   - Định tuyến đến Recommendation Node
   - State: không thay đổi

3. **Recommendation Node**: 
   - Phân tích yêu cầu tư vấn và đưa ra lời khuyên
   - Đề xuất kính có khung vuông hoặc góc cạnh để cân bằng khuôn mặt tròn
   - State: `recommendation = "..."`

4. **Kết quả**: Trả về lời khuyên về loại kính phù hợp với khuôn mặt tròn

## 5. Công nghệ và triển khai

### 5.1. Công nghệ sử dụng

Search Agent được xây dựng dựa trên nhiều công nghệ hiện đại:

1. **LangChain và LangGraph**: Framework xây dựng chuỗi xử lý và luồng công việc dạng đồ thị
   - **Vai trò**: Cung cấp cấu trúc cho việc xây dựng và quản lý các node và luồng xử lý
   - **Lợi ích**: Dễ dàng mở rộng, thay đổi và theo dõi luồng xử lý

2. **Google Gemini**: Mô hình ngôn ngữ lớn (LLM) từ Google
   - **Vai trò**: Phân loại ý định, trích xuất thuộc tính, phân tích hình ảnh, định dạng phản hồi
   - **Lợi ích**: Hiểu ngôn ngữ tự nhiên tiếng Việt, phân tích hình ảnh, linh hoạt trong xử lý

3. **CLIP (Contrastive Language-Image Pre-training)**: Mô hình đa phương thức từ OpenAI
   - **Vai trò**: Chuyển đổi văn bản và hình ảnh thành vector embedding có thể so sánh
   - **Lợi ích**: Cho phép tìm kiếm ngữ nghĩa kết hợp giữa văn bản và hình ảnh
   - **Điểm đặc biệt**: Sử dụng mô hình CLIP tùy chỉnh (CLIP_FTMT.pt) được fine-tune cho kính mắt

4. **Qdrant**: Cơ sở dữ liệu vector
   - **Vai trò**: Lưu trữ và tìm kiếm vector embedding của sản phẩm kính mắt
   - **Lợi ích**: Tìm kiếm nhanh chóng, hỗ trợ lọc theo thuộc tính, khả năng mở rộng cao

5. **FastAPI**: Framework phát triển API RESTful
   - **Vai trò**: Cung cấp giao diện API để tương tác với Search Agent
   - **Lợi ích**: Hiệu suất cao, hỗ trợ bất đồng bộ, tài liệu tự động

### 5.2. Cấu hình và triển khai

Search Agent được triển khai như một dịch vụ độc lập, có thể tương tác với các agent khác thông qua giao thức A2A (Agent-to-Agent):

1. **Cấu hình môi trường**:
   - `GOOGLE_API_KEY`: API key cho Google Gemini
   - `QDRANT_HOST`: Host của Qdrant server (mặc định: "localhost")
   - `QDRANT_PORT`: Port của Qdrant server (mặc định: 6333)
   - `CLIP_MODEL_PATH`: Đường dẫn đến mô hình CLIP tùy chỉnh

2. **API Endpoints**:
   - `POST /search`: Tìm kiếm sản phẩm với văn bản và/hoặc hình ảnh
   - `POST /search/text`: Tìm kiếm sản phẩm chỉ với văn bản
   - `GET /`: Kiểm tra trạng thái của agent

3. **A2A Endpoints**:
   - `POST /.well-known/agent.json`: Trả về Agent Card với thông tin về agent
   - `POST /`: Xử lý các yêu cầu JSON-RPC từ Host Agent

### 5.3. Mô hình CLIP tùy chỉnh

Một điểm đặc biệt của Search Agent là sử dụng mô hình CLIP tùy chỉnh (CLIP_FTMT.pt) được fine-tune đặc biệt cho lĩnh vực kính mắt:

1. **Vị trí mô hình**: `../models/clip/CLIP_FTMT.pt`

2. **Đặc điểm**:
   - Được fine-tune với dữ liệu kính mắt đa dạng
   - Hiểu được các đặc điểm và thuộc tính của kính mắt
   - Tối ưu hóa cho việc tìm kiếm kính mắt dựa trên văn bản và hình ảnh

3. **Lợi ích**:
   - Tăng độ chính xác khi tìm kiếm sản phẩm kính mắt
   - Hiểu được các thuật ngữ chuyên ngành về kính mắt
   - Nhận diện tốt hơn các đặc điểm của kính mắt trong hình ảnh
