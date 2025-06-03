# Hướng dẫn Debug Chatbot

## Cách Debug Quá Trình Xử Lý Chatbot

Chatbot này được xây dựng dựa trên LangGraph, với các node và flow xử lý rõ ràng. Hệ thống đã được bổ sung tính năng debug để theo dõi quá trình xử lý, phân tích intent và trạng thái qua từng bước.

### 1. Sử dụng Log Output

Hệ thống tự động ghi log chi tiết tới console, bao gồm:
- Node nào đang được thực thi
- Intent được phân loại là gì
- Parameters được trích xuất
- Conversation stage hiện tại
- Kết quả cuối cùng

Để xem log, chạy ứng dụng và quan sát output trong console.

### 2. Xem Debug Files

Chatbot lưu trạng thái tại mỗi bước xử lý vào thư mục `debug_logs`:
- Mỗi file được đặt tên theo định dạng: `[timestamp]_[node_name].json`
- Các file chứa trạng thái đầy đủ của hệ thống tại thời điểm node được thực thi
- File `initial_state.json` và `final_state.json` cho biết trạng thái ban đầu và cuối cùng

Thư mục `debug_logs` được tạo tự động trong thư mục bạn chạy ứng dụng.

### 3. Debug Intent Classification

Để debug quá trình phân loại intent:
- Xem các file log với tên `intent_classification_node.json`
- Kiểm tra thông tin input message và intent được phân loại
- Xem log output để biết quá trình phân loại

### 4. Debug Parameter Extraction

Để debug quá trình trích xuất tham số:
- Xem các file log với tên `parameter_extraction_node.json`
- Kiểm tra tham số được trích xuất từ message
- Tìm các trường hợp trích xuất thất bại để điều chỉnh prompt

#### Xử lý lỗi JSON trong Parameter Extraction

Khi thấy lỗi `Failed to parse parameters JSON` trong log, có thể là do:
1. LLM trả về JSON trong code block markdown (```json ... ```) thay vì JSON thuần túy
2. LLM trả về JSON không hợp lệ hoặc sai cú pháp
3. LLM chỉ trả về tên trường (ví dụ: "name") thay vì JSON đầy đủ
4. LLM trả về chuỗi sai định dạng JSON

Hệ thống hiện đã được nâng cấp với hàm `process_llm_json_output()` mạnh mẽ để xử lý các trường hợp này:

**Khả năng xử lý JSON:**
- Tự động loại bỏ code block markdown (```json ... ```)
- Xử lý trường hợp LLM chỉ trả về "name" hoặc tên trường khác
- Hỗ trợ nhiều mẫu regex khác nhau để trích xuất thông tin
- Trích xuất trực tiếp từ message gốc nếu cần
- Cung cấp default parameters cho các intent không cần tham số phức tạp
- Xử lý riêng cho từng loại intent khác nhau
- Kiểm tra định dạng JSON hợp lệ và chuyển đổi khi cần thiết

**Quy trình xử lý:**
1. Làm sạch output, loại bỏ code blocks
2. Xử lý các trường hợp đặc biệt (field name đơn lẻ)
3. Thử parse JSON tiêu chuẩn
4. Nếu thất bại, sử dụng nhiều pattern regex để trích xuất
5. Áp dụng xử lý đặc biệt theo từng intent
6. Trích xuất thông tin trực tiếp từ message gốc nếu cần
7. Fallback về default parameters

**Trích xuất tên sản phẩm thông minh:**
Hệ thống có hàm chuyên biệt `extract_product_name_from_message()` để trích xuất tên sản phẩm từ nhiều dạng câu khác nhau:
- "tìm sản phẩm tên là X"
- "X là gì"
- "cần tìm X"
- Và nhiều dạng câu khác

Nếu vẫn gặp lỗi, kiểm tra log để xem raw output của LLM và điều chỉnh prompt trong `prompts.py` hoặc thêm pattern xử lý trong `intent_nodes.py`.

### 5. Debug Flow Routing

Để theo dõi cách chatbot di chuyển qua các node:
- Xem các file log `route_by_intent.json` và `route_to_tool.json`
- Đọc log message về việc routing dựa trên intent và conversation stage
- Kiểm tra các node được gọi theo thứ tự thời gian từ timestamp trong tên file

### 6. Kích hoạt Debug Mode Nâng cao

Để có thêm thông tin debug chi tiết hơn:
1. Đổi level logging thành DEBUG trong `langgraph_bot.py`:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

2. Theo dõi prompt đầy đủ cho từng bước bằng cách bật các log DEBUG trong node implementation.

3. Sử dụng `save_debug_state()` để lưu trạng thái tại các điểm quan trọng khác nếu cần:
```python
save_debug_state(state, "custom_debug_point")
```

## Cấu trúc Node Flow

Luồng xử lý thông thường như sau:
1. `check_conversation_stage` → Kiểm tra đang ở giai đoạn conversation nào
2. `intent_classification` → Phân loại intent từ message
3. `route_by_intent` → Routing dựa trên intent hoặc conversation stage
4. `parameter_extraction` → Trích xuất tham số nếu cần thiết
5. `route_to_tool` → Routing tới tool node tương ứng
6. Tool nodes (như `find_product_by_name`, `add_to_cart`, v.v.)
7. `generate_response` → Tạo câu trả lời cuối cùng

Hãy theo dõi các file debug theo thứ tự thời gian để thấy được toàn bộ flow. 