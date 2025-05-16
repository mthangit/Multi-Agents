from .product_tools import product_tools
from .cart_tools import cart_tools
from .order_tools import order_tools

# Tạo danh sách tất cả các tools để sử dụng với agent
all_tools = []
all_tools.extend(product_tools)
all_tools.extend(cart_tools)
all_tools.extend(order_tools) 