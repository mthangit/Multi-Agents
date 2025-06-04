from typing import Dict, List, Optional, Any
from app.tools.base import Tool

class GlassesCompareTool(Tool):
    def __init__(self):
        super().__init__(
            name="glasses_compare",
            description="Công cụ so sánh các mẫu kính mắt"
        )
    
    def execute(self, glasses_list: List[Dict]) -> Dict[str, Any]:
        """
        So sánh các mẫu kính mắt
        
        Args:
            glasses_list: Danh sách các mẫu kính cần so sánh
                Mỗi mẫu kính là một Dict chứa thông tin:
                - id: ID sản phẩm
                - name: Tên sản phẩm
                - price: Giá
                - features: Danh sách tính năng
                - pros: Ưu điểm
                - cons: Nhược điểm
                
        Returns:
            Dict chứa kết quả so sánh
        """
        try:
            if len(glasses_list) < 2:
                return {
                    "success": False,
                    "error": "Cần ít nhất 2 mẫu kính để so sánh"
                }
            
            comparison = {
                "products": [],
                "price_comparison": [],
                "features_comparison": {},
                "summary": {
                    "best_value": None,
                    "most_features": None,
                    "highest_rated": None
                }
            }
            
            # So sánh giá
            min_price = float('inf')
            max_price = 0
            total_price = 0
            
            for glasses in glasses_list:
                price = float(glasses.get("price", 0))
                min_price = min(min_price, price)
                max_price = max(max_price, price)
                total_price += price
                
                comparison["products"].append({
                    "id": glasses.get("id"),
                    "name": glasses.get("name"),
                    "price": price,
                    "features": glasses.get("features", []),
                    "pros": glasses.get("pros", []),
                    "cons": glasses.get("cons", [])
                })
            
            comparison["price_comparison"] = {
                "min": min_price,
                "max": max_price,
                "average": total_price / len(glasses_list)
            }
            
            # So sánh tính năng
            all_features = set()
            for glasses in glasses_list:
                all_features.update(glasses.get("features", []))
            
            for feature in all_features:
                comparison["features_comparison"][feature] = [
                    glasses.get("id") 
                    for glasses in glasses_list 
                    if feature in glasses.get("features", [])
                ]
            
            # Tóm tắt
            if comparison["products"]:
                # Giá trị tốt nhất (giá thấp nhất với nhiều tính năng)
                best_value = min(
                    comparison["products"],
                    key=lambda x: x["price"] / (len(x["features"]) + 1)
                )
                comparison["summary"]["best_value"] = best_value["id"]
                
                # Nhiều tính năng nhất
                most_features = max(
                    comparison["products"],
                    key=lambda x: len(x["features"])
                )
                comparison["summary"]["most_features"] = most_features["id"]
                
                # Đánh giá cao nhất (ít nhược điểm nhất)
                highest_rated = min(
                    comparison["products"],
                    key=lambda x: len(x["cons"])
                )
                comparison["summary"]["highest_rated"] = highest_rated["id"]
            
            return {
                "success": True,
                "comparison": comparison
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Lỗi khi so sánh: {str(e)}"
            } 