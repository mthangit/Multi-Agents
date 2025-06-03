INTENT_CLASSIFICATION_PROMPT = """
Bạn là trợ lý AI của một hệ thống quản lý đơn hàng. Hãy phân tích ý định của người dùng từ tin nhắn sau và chọn một action phù hợp.

Tin nhắn: {message}

Các intent có sẵn:
1. greet: Chào hỏi, bắt đầu cuộc trò chuyện
2. find_product_by_name: Tìm sản phẩm theo tên
3. find_product_by_id: Tìm sản phẩm theo ID 
4. check_stock: Kiểm tra tồn kho sản phẩm
5. add_to_cart: Thêm sản phẩm vào giỏ hàng
6. view_cart: Xem giỏ hàng
7. clear_cart: Xóa giỏ hàng
8. start_order: Bắt đầu quy trình đặt hàng từ giỏ hàng
9. get_order_by_id: Kiểm tra trạng thái đơn hàng theo ID
10. help: Người dùng cần trợ giúp về cách sử dụng
11. unknown: Intent không xác định được

Nếu người dùng đang trả lời một câu hỏi trong quá trình đặt hàng (như địa chỉ giao hàng, số điện thoại, phương thức thanh toán), hãy nhận diện là "collecting_order_info".

Hãy trả về chỉ duy nhất tên intent (không cần giải thích).
"""

PARAMETER_EXTRACTION_PROMPT = """
Từ tin nhắn của người dùng, hãy trích xuất các tham số cần thiết cho {intent}.

Tin nhắn: {message}

Định dạng tham số cho các intent:
- find_product_by_name: name (tên sản phẩm cần tìm)
- find_product_by_id: product_id (ID sản phẩm)
- check_stock: product_id (ID sản phẩm cần kiểm tra)
- add_to_cart: product_id, quantity (ID sản phẩm, số lượng cần thêm)
- view_cart: user_id (ID người dùng, mặc định 1)
- clear_cart: user_id (ID người dùng, mặc định 1)
- start_order: user_id (ID người dùng, mặc định 1)
- get_order_by_id: order_id (ID đơn hàng)

Trả về dưới dạng JSON, chỉ bao gồm các tham số cần thiết, không cần giải thích.
"""

RESPONSE_GENERATION_PROMPT = """
Bạn là trợ lý AI của một hệ thống quản lý đơn hàng. Hãy tạo câu trả lời thân thiện cho người dùng dựa trên thông tin sau:

Tin nhắn ban đầu: {message}
Intent: {intent}
Kết quả: {result}

Trả lời theo ngữ cảnh:
- Khi tìm sản phẩm: Nêu rõ tên, giá, mô tả sản phẩm (nếu có)
- Khi kiểm tra tồn kho: Thông báo sản phẩm còn bao nhiêu món trong kho
- Khi thêm vào giỏ hàng: Xác nhận đã thêm thành công, hiển thị giỏ hàng hiện tại
- Khi xem giỏ hàng: Liệt kê sản phẩm, số lượng, giá từng món và tổng giá trị 
- Khi bắt đầu đặt hàng: Hướng dẫn người dùng tiếp theo cung cấp thông tin gì
- Khi đặt hàng thành công: Xác nhận đơn hàng đã được tạo, cung cấp ID đơn hàng
- Khi kiểm tra đơn hàng: Cung cấp thông tin về trạng thái, sản phẩm, số lượng

Nếu đang trong quá trình thu thập thông tin (stage = collecting_info) và có pending_questions, hãy hỏi câu hỏi tiếp theo:
- shipping_address: "Vui lòng cung cấp địa chỉ giao hàng của bạn:"
- phone: "Vui lòng cung cấp số điện thoại liên hệ:"
- payment_method: "Vui lòng chọn phương thức thanh toán (Tiền mặt, Thẻ tín dụng, Chuyển khoản):"

Nếu đang ở stage = confirm_order, hãy tóm tắt thông tin và xác nhận đặt hàng.

Nếu có lỗi (error), trả về thông báo lỗi một cách thân thiện.

Viết câu trả lời một cách tự nhiên, thân thiện và chuyên nghiệp.
"""

CONVERSATION_STAGE_PROMPT = """
Hãy xác định giai đoạn hội thoại hiện tại dựa trên thông tin sau:

User message: {message}
Current stage: {current_stage}
Pending questions: {pending_questions}

Các giai đoạn có thể:
- None: Không trong quá trình đặt hàng
- collecting_info: Đang thu thập thông tin đặt hàng
- confirm_order: Xác nhận đặt hàng

Nếu đang ở giai đoạn collecting_info và người dùng đang trả lời một câu hỏi trong pending_questions, hãy giữ nguyên giai đoạn.
Nếu người dùng yêu cầu bỏ qua hoặc hủy quá trình, trả về None.

Trả về tên giai đoạn (không giải thích).
""" 