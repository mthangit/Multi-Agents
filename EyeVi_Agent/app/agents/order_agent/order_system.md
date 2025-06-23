# Hệ thống Order Agent trong EyeVi Multi-Agent

## Tóm tắt

Tài liệu này mô tả chi tiết về Order Agent, một thành phần quan trọng trong hệ thống EyeVi Multi-Agent. Order Agent được thiết kế để quản lý quy trình đặt hàng, tìm kiếm sản phẩm, và xử lý đơn hàng thông qua giao diện hội thoại tự nhiên. Tài liệu sẽ trình bày kiến trúc, chức năng chính, luồng xử lý, và các thành phần kỹ thuật của Order Agent.

## 1. Giới thiệu

Order Agent là một agent thông minh được phát triển để hỗ trợ người dùng trong việc tìm kiếm sản phẩm và tạo đơn hàng thông qua giao diện hội thoại tự nhiên. Agent được xây dựng dựa trên LangGraph, một framework cho phép tạo ra các luồng xử lý phức tạp với các mô hình ngôn ngữ lớn (LLM). Order Agent đóng vai trò là cầu nối giữa người dùng và hệ thống cơ sở dữ liệu, giúp người dùng dễ dàng tương tác với hệ thống thông qua ngôn ngữ tự nhiên.

## 2. Kiến trúc tổng quan

```
┌─────────────────────────────┐
│      Người dùng (User)      │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│      LangGraph Workflow     │
│  ┌───────────┐ ┌─────────┐  │
│  │ Assistant │ │  Tools  │  │
│  │   Node    │ │  Node   │  │
│  └───────────┘ └─────────┘  │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│           Tools             │
│  ┌───────────────────────┐  │
│  │ - find_product_by_id  │  │
│  │ - find_product_by_name│  │
│  │ - get_user_info       │  │
│  │ - get_user_orders     │  │
│  │ - create_order        │  │
│  │ - update_order_info   │  │
│  └───────────────────────┘  │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│         Database            │
│  ┌───────────┐ ┌─────────┐  │
│  │ Products  │ │  Users  │  │
│  └───────────┘ └─────────┘  │
│  ┌───────────┐ ┌─────────┐  │
│  │  Orders   │ │ Details │  │
│  └───────────┘ └─────────┘  │
└─────────────────────────────┘
```

Order Agent được tổ chức theo mô hình phân lớp với các thành phần chính:

1. **Giao diện người dùng**: Tiếp nhận đầu vào từ người dùng dưới dạng tin nhắn văn bản.
2. **LangGraph Workflow**: Xử lý luồng hội thoại thông qua hai node chính:
   - **Assistant Node**: Phân tích yêu cầu của người dùng và quyết định công cụ cần sử dụng.
   - **Tools Node**: Thực thi các công cụ được chọn và trả kết quả về Assistant Node.
3. **Tools**: Các công cụ chức năng để thực hiện các tác vụ cụ thể.
4. **Database**: Lưu trữ và quản lý dữ liệu về sản phẩm, người dùng và đơn hàng.

## 3. Chức năng chính

Order Agent cung cấp 6 chức năng chính:

1. **Tìm sản phẩm theo ID**: Tìm kiếm và hiển thị thông tin chi tiết của sản phẩm dựa trên ID.
2. **Tìm sản phẩm theo tên**: Tìm kiếm các sản phẩm có tên chứa từ khóa được cung cấp.
3. **Lấy thông tin người dùng**: Hiển thị thông tin chi tiết của người dùng dựa trên ID.
4. **Lấy lịch sử đơn hàng**: Hiển thị danh sách đơn hàng gần đây của người dùng.
5. **Tạo đơn hàng trực tiếp**: Tạo đơn hàng mới với danh sách sản phẩm, địa chỉ giao hàng và phương thức thanh toán.
6. **Cập nhật thông tin đơn hàng**: Cập nhật thông tin giao hàng và phương thức thanh toán của đơn hàng.

## 4. Luồng xử lý

### 4.1. Luồng xử lý chung

1. Người dùng gửi tin nhắn văn bản đến Order Agent.
2. Assistant Node phân tích tin nhắn và xác định ý định của người dùng.
3. Nếu cần sử dụng công cụ, Assistant Node gọi Tools Node.
4. Tools Node thực thi công cụ tương ứng và trả kết quả về Assistant Node.
5. Assistant Node tổng hợp kết quả và trả lời người dùng.

### 4.2. Luồng tạo đơn hàng

Quy trình tạo đơn hàng được thực hiện qua 4 bước:

1. **Query thông tin sản phẩm**: Kiểm tra thông tin sản phẩm từ cơ sở dữ liệu.
2. **Kiểm tra tồn kho và tính tiền**: Xác nhận số lượng tồn kho và tính tổng giá trị đơn hàng.
3. **Tạo đơn hàng**: Sau khi xác thực, đơn hàng được tạo trong cơ sở dữ liệu.
4. **Xác nhận thông tin**: Xác nhận lại thông tin với người dùng và cập nhật nếu cần.

## 5. Thành phần kỹ thuật

### 5.1. Mô hình ngôn ngữ

Order Agent sử dụng mô hình Gemini 2.0 Flash từ Google để xử lý ngôn ngữ tự nhiên:

```python
self.llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", 
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.1
)
```

### 5.2. Công cụ (Tools)

Order Agent định nghĩa 6 công cụ chính:

```python
self.tools = [
    find_product_by_id, 
    find_product_by_name,
    get_user_info,
    get_user_orders,
    create_order_directly,
    update_order_info
]
```

### 5.3. LangGraph Workflow

Workflow được tổ chức với 2 node chính và luồng xử lý đơn giản:

```python
workflow = StateGraph(SimpleOrderState)
workflow.add_node("assistant", self._assistant_node)
workflow.add_node("tools", self._tools_node)
workflow.add_edge(START, "assistant")
workflow.add_conditional_edges(
    "assistant",
    self._should_use_tools,
    {
        "tools": "tools",
        "end": END
    }
)
workflow.add_edge("tools", "assistant")
```

### 5.4. Cơ sở dữ liệu

Order Agent tương tác với cơ sở dữ liệu thông qua các lớp truy vấn:

- **ProductQuery**: Quản lý truy vấn thông tin sản phẩm.
- **UserQuery**: Quản lý truy vấn thông tin người dùng.
- **OrderQuery**: Quản lý truy vấn và xử lý đơn hàng.

## 6. Định dạng dữ liệu

Order Agent sử dụng định dạng dữ liệu đặc biệt khi trả kết quả, bao gồm:

1. **Text hiển thị**: Thông tin được định dạng đẹp mắt để hiển thị cho người dùng.
2. **Data JSON**: Dữ liệu cấu trúc được đánh dấu bằng `[DATA_MARKER]` để client xử lý.

Ví dụ:
```
✅ Sản phẩm tìm thấy:
📦 ID: 1
🏷️ Tên: iPhone 15 Pro
💰 Giá: 30,000,000 VND
📝 Mô tả: Điện thoại cao cấp nhất của Apple
📊 Tồn kho: 10 sản phẩm

[DATA_MARKER]{"type":"product_detail","data":{"id":1,"name":"iPhone 15 Pro","price":30000000,"description":"Điện thoại cao cấp nhất của Apple","stock":10}}[/DATA_MARKER]
```

## 7. Hiệu suất và giới hạn

### 7.1. Hiệu suất

- **Thời gian phản hồi**: Trung bình dưới 2 giây cho mỗi yêu cầu.
- **Sử dụng bộ nhớ**: Khoảng 50MB cho mỗi phiên.
- **Khả năng mở rộng**: Hỗ trợ hơn 50 người dùng đồng thời.

### 7.2. Giới hạn

- Chỉ hỗ trợ tiếng Việt.
- Không hỗ trợ xử lý hình ảnh sản phẩm.
- Giới hạn 5 sản phẩm khi hiển thị kết quả tìm kiếm.

## 8. Bảo mật

Order Agent thực hiện các biện pháp bảo mật sau:

- Xác thực người dùng thông qua ID.
- Kiểm tra tính hợp lệ của dữ liệu đầu vào.
- Sử dụng prepared statements để ngăn chặn SQL injection.
- Xử lý lỗi an toàn để tránh lộ thông tin nhạy cảm.

## 9. Kết luận

Order Agent là một thành phần quan trọng trong hệ thống EyeVi Multi-Agent, cung cấp giao diện hội thoại tự nhiên để người dùng tìm kiếm sản phẩm và tạo đơn hàng. Với kiến trúc dựa trên LangGraph và khả năng tương tác với cơ sở dữ liệu, Order Agent mang lại trải nghiệm mua sắm liền mạch và hiệu quả cho người dùng.

## Tài liệu tham khảo

1. LangGraph Documentation: [https://langchain-ai.github.io/langgraph/](https://langchain-ai.github.io/langgraph/)
2. Google Generative AI: [https://ai.google.dev/](https://ai.google.dev/)
3. EyeVi Multi-Agent System Documentation (internal)
