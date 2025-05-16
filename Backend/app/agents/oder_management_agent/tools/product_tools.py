"""
Product tools module
"""
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from shopping_agent.services.product_service import ProductService
from shopping_agent.tools.base import create_db_tool, ToolRegistry

# Tool functions
def search_products(db: Session, query: Optional[str] = None, 
                    category: Optional[str] = None, 
                    brand: Optional[str] = None, 
                    min_price: Optional[float] = None, 
                    max_price: Optional[float] = None) -> Dict[str, Any]:
    """
    Tìm kiếm sản phẩm theo các tiêu chí
    
    Args:
        db: Database session
        query: Từ khóa tìm kiếm
        category: Danh mục sản phẩm
        brand: Thương hiệu
        min_price: Giá tối thiểu
        max_price: Giá tối đa
        
    Returns:
        Dict với kết quả tìm kiếm
    """
    return ProductService.search_products(db, query, category, brand, min_price, max_price)

def get_product_details(db: Session, product_id: int) -> Dict[str, Any]:
    """
    Lấy chi tiết sản phẩm
    
    Args:
        db: Database session
        product_id: ID sản phẩm
        
    Returns:
        Dict với thông tin chi tiết sản phẩm
    """
    return ProductService.get_product_details(db, product_id)

def check_product_stock(db: Session, product_id: int) -> Dict[str, Any]:
    """
    Kiểm tra tồn kho sản phẩm
    
    Args:
        db: Database session
        product_id: ID sản phẩm
        
    Returns:
        Dict với thông tin tồn kho
    """
    return ProductService.check_stock(db, product_id)

def get_product_recommendations(db: Session, product_id: int, limit: int = 5) -> Dict[str, Any]:
    """
    Đề xuất sản phẩm tương tự
    
    Args:
        db: Database session
        product_id: ID sản phẩm
        limit: Số lượng sản phẩm đề xuất
        
    Returns:
        Dict với danh sách sản phẩm đề xuất
    """
    return ProductService.get_recommendations(db, product_id, limit)

# Tạo các tools
search_products_tool = create_db_tool(
    name="search_products",
    description="Tìm kiếm sản phẩm theo từ khóa, danh mục, thương hiệu và khoảng giá",
    func=search_products
)

get_product_details_tool = create_db_tool(
    name="get_product_details",
    description="Lấy thông tin chi tiết của một sản phẩm",
    func=get_product_details
)

check_product_stock_tool = create_db_tool(
    name="check_product_stock",
    description="Kiểm tra số lượng sản phẩm trong kho",
    func=check_product_stock
)

get_product_recommendations_tool = create_db_tool(
    name="get_product_recommendations",
    description="Đề xuất các sản phẩm tương tự với sản phẩm được chỉ định",
    func=get_product_recommendations
)

# Tạo danh sách tools
product_tools = [
    search_products_tool,
    get_product_details_tool,
    check_product_stock_tool,
    get_product_recommendations_tool
]

# Đăng ký tools vào registry
ToolRegistry.register_tools("product", product_tools)
