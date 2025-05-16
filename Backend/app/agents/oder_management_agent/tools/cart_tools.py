from google.adk.tools import Tool
from ..services.cart_service import CartService

def add_to_cart(user_id: int, product_id: str, quantity: int) -> dict:
    """Thêm sản phẩm vào giỏ hàng
    
    Args:
        user_id (int): ID của người dùng
        product_id (str): ID của sản phẩm
        quantity (int): Số lượng sản phẩm
        
    Returns:
        dict: Kết quả thêm vào giỏ hàng
    """
    return CartService.add_item(user_id, product_id, quantity)

def remove_from_cart(user_id: int, product_id: str) -> dict:
    """Xóa sản phẩm khỏi giỏ hàng
    
    Args:
        user_id (int): ID của người dùng
        product_id (str): ID của sản phẩm
        
    Returns:
        dict: Kết quả xóa khỏi giỏ hàng
    """
    return CartService.remove_item(user_id, product_id)

def update_cart_item(user_id: int, product_id: str, quantity: int) -> dict:
    """Cập nhật số lượng sản phẩm trong giỏ hàng
    
    Args:
        user_id (int): ID của người dùng
        product_id (str): ID của sản phẩm
        quantity (int): Số lượng mới
        
    Returns:
        dict: Kết quả cập nhật giỏ hàng
    """
    return CartService.update_quantity(user_id, product_id, quantity)

def get_cart(user_id: int) -> dict:
    """Lấy thông tin giỏ hàng của người dùng
    
    Args:
        user_id (int): ID của người dùng
        
    Returns:
        dict: Thông tin giỏ hàng
    """
    return CartService.get_cart(user_id)

cart_tools = [
    Tool(
        name="add_to_cart",
        description="Thêm sản phẩm vào giỏ hàng",
        function=add_to_cart
    ),
    Tool(
        name="remove_from_cart",
        description="Xóa sản phẩm khỏi giỏ hàng",
        function=remove_from_cart
    ),
    Tool(
        name="update_cart_item",
        description="Cập nhật số lượng sản phẩm trong giỏ hàng",
        function=update_cart_item
    ),
    Tool(
        name="get_cart",
        description="Lấy thông tin giỏ hàng của người dùng",
        function=get_cart
    )
] 