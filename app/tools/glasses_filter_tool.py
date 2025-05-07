from typing import Dict, List, Optional, Any
from app.tools.base import Tool

class GlassesFilterTool(Tool):
    def __init__(self):
        super().__init__(
            name="glasses_filter",
            description="Công cụ lọc kết quả tìm kiếm kính mắt"
        )
    
    def execute(self, results: List[Dict], filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Lọc kết quả tìm kiếm kính mắt dựa trên các tiêu chí
        
        Args:
            results: Danh sách kết quả tìm kiếm
            filters: Dict chứa các tiêu chí lọc
                - gender: Giới tính (nam/nữ)
                - style: Kiểu dáng (gọng nhựa/gọng kim loại)
                - color: Màu sắc
                - price_range: Khoảng giá (min, max)
                
        Returns:
            Dict chứa kết quả đã lọc
        """
        try:
            filtered_results = results.copy()
            
            # Lọc theo giới tính
            if "gender" in filters:
                gender = filters["gender"].lower()
                filtered_results = [
                    r for r in filtered_results 
                    if r.get("gender", "").lower() == gender
                ]
            
            # Lọc theo kiểu dáng
            if "style" in filters:
                style = filters["style"].lower()
                filtered_results = [
                    r for r in filtered_results 
                    if r.get("style", "").lower() == style
                ]
            
            # Lọc theo màu sắc
            if "color" in filters:
                color = filters["color"].lower()
                filtered_results = [
                    r for r in filtered_results 
                    if r.get("color", "").lower() == color
                ]
            
            # Lọc theo khoảng giá
            if "price_range" in filters:
                min_price, max_price = filters["price_range"]
                filtered_results = [
                    r for r in filtered_results 
                    if min_price <= r.get("price", 0) <= max_price
                ]
            
            return {
                "success": True,
                "results": filtered_results,
                "total": len(filtered_results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Lỗi khi lọc kết quả: {str(e)}"
            } 