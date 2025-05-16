from google.adk.tools import Tool
from ..services.order_service import OrderService

def create_order(user_id: int, address_id: int, payment_method: str) -> dict:
    """Tạo đơn hàng mới
    
    Args:
        user_id (int): ID của người dùng
        address_id (int): ID của địa chỉ giao hàng
        payment_method (str): Phương thức thanh toán
        
    Returns:
        dict: Thông tin đơn hàng đã tạo
    """
    return OrderService.create_order(user_id, address_id, payment_method)

def get_order_status(order_id: int) -> dict:
    """Lấy trạng thái đơn hàng
    
    Args:
        order_id (int): ID của đơn hàng
        
    Returns:
        dict: Trạng thái đơn hàng
    """
    return OrderService.get_status(order_id)

def get_user_orders(user_id: int) -> dict:
    """Lấy danh sách đơn hàng của người dùng
    
    Args:
        user_id (int): ID của người dùng
        
    Returns:
        dict: Danh sách đơn hàng
    """
    return OrderService.get_user_orders(user_id)

def cancel_order(order_id: int) -> dict:
    """Hủy đơn hàng
    
    Args:
        order_id (int): ID của đơn hàng
        
    Returns:
        dict: Kết quả hủy đơn hàng
    """
    return OrderService.cancel_order(order_id)

