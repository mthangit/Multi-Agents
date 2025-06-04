from src.database.queries.cart import CartQuery
from src.database.queries.product import ProductQuery
from src.database.queries.order import OrderQuery

def check_stock_node(state):
    """Kiểm tra tồn kho sản phẩm trước khi thêm vào giỏ hàng"""
    parameters = state.get("parameters", {})
    product_id = parameters.get("product_id")
    
    if not product_id:
        return {"error": "Không tìm thấy ID sản phẩm"}
    
    product = OrderQuery().check_stock(product_id)
    
    if not product:
        return {"error": f"Không tìm thấy sản phẩm với ID {product_id}"}
    
    if product['stock'] <= 0:
        return {
            "product": product,
            "error": f"Sản phẩm '{product['name']}' đã hết hàng"
        }
    
    # Thành công - trả về thông tin sản phẩm
    return {"product": product}

def add_to_cart_node(state):
    """Thêm sản phẩm vào giỏ hàng"""
    parameters = state.get("parameters", {})
    product_id = parameters.get("product_id")
    user_id = parameters.get("user_id", 1)  # Default user_id = 1 cho test
    quantity = parameters.get("quantity", 1)
    
    # Kiểm tra sản phẩm
    product = state.get("product")
    if not product:
        return {"error": "Không có thông tin sản phẩm để thêm vào giỏ hàng"}
    
    # Kiểm tra số lượng tồn kho
    if quantity > product['stock']:
        return {"error": f"Không đủ hàng. Chỉ còn {product['stock']} sản phẩm."}
    
    # Thêm vào giỏ hàng
    success = CartQuery().add_to_cart(user_id, product_id, quantity)
    
    if not success:
        return {"error": "Không thể thêm vào giỏ hàng"}
    
    # Lấy giỏ hàng hiện tại
    cart_items = CartQuery().get_cart_items(user_id)
    
    return {"cart_items": cart_items}

def view_cart_node(state):
    """Xem giỏ hàng hiện tại"""
    parameters = state.get("parameters", {})
    user_id = parameters.get("user_id", 1)  # Default user_id = 1 cho test
    
    cart_items = CartQuery().get_cart_items(user_id)
    
    return {"cart_items": cart_items}

def clear_cart_node(state):
    """Xóa toàn bộ giỏ hàng"""
    parameters = state.get("parameters", {})
    user_id = parameters.get("user_id", 1)  # Default user_id = 1 cho test
    
    success = CartQuery().clear_cart(user_id)
    
    if not success:
        return {"error": "Không thể xóa giỏ hàng"}
    
    return {"cart_items": []} 