from src.database.queries.order import OrderQuery
from src.database.queries.cart import CartQuery

def start_order_process_node(state):
    """Khởi động quá trình đặt hàng: Kiểm tra giỏ hàng và bắt đầu thu thập thông tin"""
    parameters = state.get("parameters", {})
    user_id = parameters.get("user_id", 1)  # Default user_id = 1 cho test
    
    # Kiểm tra giỏ hàng
    cart_items = CartQuery().get_cart_items(user_id)
    
    if not cart_items:
        return {
            "error": "Giỏ hàng trống. Vui lòng thêm sản phẩm vào giỏ trước khi đặt hàng.",
            "conversation_stage": None
        }
    
    # Thiết lập quá trình thu thập thông tin
    pending_questions = [
        "shipping_address",
        "phone",
        "payment_method"
    ]
    
    return {
        "cart_items": cart_items,
        "conversation_stage": "collecting_info",
        "pending_questions": pending_questions,
        "collected_info": {"user_id": user_id}
    }

def collect_order_info_node(state):
    """Thu thập thông tin đặt hàng từ người dùng"""
    message = state.get("message", "")
    pending_questions = state.get("pending_questions", [])
    collected_info = state.get("collected_info", {})
    
    if not pending_questions:
        # Đã thu thập đủ thông tin
        return {
            "conversation_stage": "confirm_order"
        }
    
    # Lấy câu hỏi hiện tại
    current_question = pending_questions[0]
    
    # Lưu câu trả lời
    collected_info[current_question] = message
    
    # Cập nhật danh sách câu hỏi
    pending_questions = pending_questions[1:]
    
    return {
        "pending_questions": pending_questions,
        "collected_info": collected_info
    }

def create_order_node(state):
    """Tạo đơn hàng từ thông tin đã thu thập"""
    collected_info = state.get("collected_info", {})
    
    # Kiểm tra thông tin đã đầy đủ chưa
    required_fields = ["user_id", "shipping_address", "phone", "payment_method"]
    for field in required_fields:
        if field not in collected_info or not collected_info[field]:
            return {
                "error": f"Thiếu thông tin {field}",
                "conversation_stage": "collecting_info"
            }
    
    try:
        # Tạo đơn hàng
        order_id = OrderQuery().create_order_from_cart(
            user_id=collected_info["user_id"],
            shipping_address=collected_info["shipping_address"],
            phone=collected_info["phone"],
            payment_method=collected_info["payment_method"]
        )
        
        if not order_id:
            return {"error": "Không thể tạo đơn hàng. Giỏ hàng trống."}
        
        # Lấy thông tin đơn hàng
        order = OrderQuery().get_order_by_id(order_id)
        
        # Kết thúc quá trình đặt hàng
        return {
            "order_id": order_id,
            "order": order,
            "conversation_stage": None,
            "collected_info": {},
            "pending_questions": []
        }
    except Exception as e:
        return {
            "error": str(e),
            "conversation_stage": None
        } 