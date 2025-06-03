from src.database.queries.product import ProductQuery
from src.database.queries.order import OrderQuery
import logging
logger = logging.getLogger("chatbot_debug")

def find_product_by_id_node(state):
    """Node để tìm sản phẩm theo ID từ parameters trong state"""
    parameters = state.get("parameters", {})
    product_id = parameters.get("product_id")
    
    if not product_id:
        return {"product": None, "error": "Không tìm thấy ID sản phẩm"}
    
    product = ProductQuery().get_product_by_id(product_id)
    return {"product": product}

def find_product_by_name_node(state):
    """Node để tìm sản phẩm theo tên từ parameters trong state"""
    parameters = state.get("parameters", {})
    name = parameters.get("name")

    logger.info(f"Tên sản phẩm: {name}")
    
    if not name:
        return {"products": [], "error": "Không tìm thấy tên sản phẩm"}
    
    products = ProductQuery().get_product_by_name(name)
    return {"products": products}

def create_order_node(state):
    """Node để tạo đơn hàng mới từ parameters trong state"""
    parameters = state.get("parameters", {})
    user_id = parameters.get("user_id")
    product_id = parameters.get("product_id")
    quantity = parameters.get("quantity")
    
    if not all([user_id, product_id, quantity]):
        return {"error": "Thiếu thông tin để tạo đơn hàng"}
    
    order_id = OrderQuery().create_order(user_id, product_id, quantity)
    return {"order_id": order_id}

def get_order_by_id_node(state):
    """Node để lấy thông tin đơn hàng theo ID từ parameters trong state"""
    parameters = state.get("parameters", {})
    order_id = parameters.get("order_id")
    
    if not order_id:
        return {"order": None, "error": "Không tìm thấy ID đơn hàng"}
    
    order = OrderQuery().get_order_by_id(order_id)
    return {"order": order} 