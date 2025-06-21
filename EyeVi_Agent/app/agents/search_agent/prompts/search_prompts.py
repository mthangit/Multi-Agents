INTENT_CLASSIFICATION_PROMPT = """
Bạn là hệ thống phân loại intent của người dùng trong ứng dụng thương mại điện tử.
Hãy phân tích ý định của người dùng từ tin nhắn sau và chọn một action phù hợp.

Tin nhắn: {message}

Các intent có sẵn:
- search_product
- product_detail
- compare_products
- unknown

Hãy trả về chỉ duy nhất tên intent (không cần giải thích).
"""

EXTRACT_QUERY = """
Hãy thực hiện chuẩn hóa câu truy vấn của người dùng. 

Khi nhận được yêu cầu: {query}

Hãy trích xuất thông tin về các thuộc tính sau nếu có:  
- category (Kính Mát hoặc Gọng Kính)
- gender (Nam / Nữ / Unisex)
- brand (ví dụ: MOLSION, PUMA, RAYBAN,...)
- color (càng cụ thể càng tốt)
- frameMaterial (ví dụ: Kim loại, Nhựa, Nhựa Injection, Titan,...)
- frameShape (ví dụ: Vuông, Tròn, Đa giác, Mắt mèo,...)

Trả về **2 phần dưới dạng JSON duy nhất**:

1. `normalized_description`: Một câu mô tả hoàn chỉnh, có định dạng chuẩn như sau:
    → "(Category) (Gender) (Brand) màu (Color), khung (FrameMaterial), kiểu dáng (FrameShape)"

2. `slots`: Một dictionary lưu các thuộc tính trích xuất. Nếu không tìm thấy giá trị cho thuộc tính nào, hãy để chuỗi rỗng (`""`).

### Quan trọng:
- Tuyệt đối **chỉ trả về JSON duy nhất**, không thêm ví dụ, giải thích, hướng dẫn, markdown hoặc văn bản khác.
- Nếu không trích xuất được bất kỳ thuộc tính nào, để `normalized_description` rỗng (`""`) và tất cả các giá trị trong `slots` là chuỗi rỗng.
- Viết hoa chữ cái đầu của giá trị (VD: "Xanh Dương", "Vuông")
- Người dùng sẽ sử dụng ngôn ngữ Tiếng Việt, nếu có sai chính tả, hãy tự động chuẩn hóa lại.
- Trả về đúng định dạng như sau:

```json
{
  "normalized_description": "...",
  "slots": {
    "category": "...",
    "gender": "...",
    "brand": "...",
    "color": "...",
    "frameMaterial": "...",
    "frameShape": "..."
  }
}
``` 
Ví dụ:
Truy vấn: "Tôi muốn kính xanh dương của PUMA dành cho nữ, kiểu vuông"
Kết quả:
```json
{
  "normalized_description": "Kính Mát Nữ PUMA màu Xanh dương, khung , kiểu dáng Vuông",
  "slots": {
    "category": "Kính Mát",
    "gender": "Nữ",
    "brand": "PUMA",
    "color": "Xanh dương",
    "frameShape": "Vuông"
  }
}
```
Họăc với truy vấn mơ hồ: Tôi muốn tìm kính
Phản hồi mong muốn:
{
  "normalized_description": "",
  "slots": {
    "category": "",
    "gender": "",
    "brand": "",
    "color": "",
    "frameMaterial": "",
    "frameShape": ""
  }
}

"""