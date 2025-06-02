INTENT_CLASSIFICATION_PROMPT = """
Bạn là hệ thống phân loại intent của người dùng trong ứng dụng thương mại điện tử.
Hãy phân tích ý định của người dùng từ tin nhắn sau và chọn một action phù hợp.

Tin nhắn: {message}

Các intent có sẵn:
- search_product
- product_detail
- compare_products
- filter_by_feature
- faq_about_material
- availability_check
- recommendation_request
- product_category_stats
- unknown

Hãy trả về chỉ duy nhất tên intent (không cần giải thích).
"""

EXTRACT_QUERY = """
Bạn là một trợ lý AI giúp chuẩn hóa truy vấn tìm kiếm kính mắt của người dùng.
Khi nhận được yêu cầu: {query}
Hãy trích xuất thông tin về các thuộc tính sau nếu có:  
- category (Kính Mát hoặc Gọng Kính)
- gender (Nam / Nữ / Unisex)
- brand (ví dụ: MOLSION, PUMA, RAYBAN,...)
- color (càng cụ thể càng tốt)
- frameMaterial (ví dụ: Kim loại, Nhựa, Nhựa Injection, Titan,...)
- frameShape (ví dụ: Vuông, Tròn, Đa giác, Mắt mèo,...)

Hãy trả về 2 phần:
1. `normalized_description` (một câu mô tả hoàn chỉnh, có định dạng chuẩn sau):
    => "(Category) (Gender) (Brand) màu (Color), khung (FrameMaterial), kiểu dáng (FrameShape)"

2. `slots`: Dạng dictionary lưu thông tin được trích xuất. Nếu không rõ, để chuỗi rỗng.

### Chú ý:
- Nếu thiếu thuộc tính nào, không xuất hiện trong câu mô tả, rút gọn lại, bỏ dấy phẩy và từ bổ nghĩa.
- Viết hoa chữ cái đầu của các giá trị (ví dụ: "Xanh Dương", "Vuông")
- Người dùng sẽ sử dụng ngôn ngữ Tiếng Việt, nếu có sai chính tả, hãy chuẩn hóa lại theo kiến thức của bạn.

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
"""