from typing import Dict, Any, Optional, List
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class FormatResponseNode:
    """Node xử lý kết quả tìm kiếm và tạo phản hồi cho client."""
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Xử lý kết quả tìm kiếm và tạo phản hồi.
        
        Args:
            state: Trạng thái hiện tại của workflow
            
        Returns:
            Dict chứa phản hồi đã được định dạng
        """
        # Lấy thông tin từ state
        search_results = state.get("search_results", [])
        query = state.get("query", "")
        normalized_query = state.get("normalized_query", "")
        extracted_attributes = state.get("extracted_attributes", {})
        
        # Lấy recommended_shapes từ extracted_attributes
        recommended_shapes = extracted_attributes.get("recommended_shapes", [])
        
        # Định dạng kết quả
        formatted_response = self._format_search_results(
            results=search_results,
            query_text=query or normalized_query,
            recommended_shapes=recommended_shapes
        )
        
        # Thêm thông tin bổ sung
        formatted_response["extracted_attributes"] = extracted_attributes
        
        return {"final_response": formatted_response}
    
    def _format_search_results(
        self, 
        results: List[Dict[str, Any]], 
        query_text: Optional[str] = None,
        recommended_shapes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Định dạng kết quả tìm kiếm thành JSON phù hợp.
        
        Args:
            results: Danh sách kết quả tìm kiếm
            query_text: Văn bản tìm kiếm ban đầu
            recommended_shapes: Các hình dạng gọng kính được đề xuất
            
        Returns:
            Kết quả được định dạng thành JSON
        """
        products = []
        for product in results:
            products.append({
                "product_id": product.get("product_id", ""),
                "name": product.get("name", ""),
                "brand": product.get("brand", ""),
                "price": product.get("price", 0),
                "description": product.get("description", ""),
                "image_url": product.get("images", [""])[0] if product.get("images") else "",
                "frame_color": product.get("color", ""),
                "category": product.get("category", ""),
                "gender": product.get("gender", ""),
                "score": product.get("score", 0),
            })
        
        # Tạo summary dựa trên kết quả
        if not products:
            summary = "Không tìm thấy sản phẩm phù hợp."
        else:
            summary_parts = []
            
            # Thêm thông tin về danh mục sản phẩm nếu có
            categories = set(p["category"] for p in products if p["category"])
            if categories:
                summary_parts.append(f"danh mục {', '.join(categories)}")
            
            # Nếu có recommended_shapes, thêm vào summary
            if recommended_shapes:
                shapes_text = ", ".join(recommended_shapes)
                summary_parts.append(f"dựa trên phân tích khuôn mặt của bạn, chúng tôi đề xuất gọng kính dạng {shapes_text}")
            
            # Thêm thông tin về số lượng sản phẩm tìm thấy
            summary_parts.append(f"đã tìm thấy {len(products)} sản phẩm phù hợp")
            
            # Nếu có query_text, thêm vào summary
            if query_text:
                summary_parts.append(f"với yêu cầu '{query_text}'")
            
            # Thông tin về thương hiệu
            brands = set(p["brand"] for p in products if p["brand"])
            if brands and len(brands) <= 3:
                summary_parts.append(f"thương hiệu {', '.join(brands)}")
            
            # Liệt kê 3 sản phẩm đầu tiên
            if products:
                top_products = products[:3]
                product_mentions = [f"{p['brand']} {p['name']}" for p in top_products]
                summary_parts.append(f"bao gồm {', '.join(product_mentions)}")
            
            summary = ". ".join(summary_parts).capitalize() + "."
        
        return {
            "products": products,
            "query": query_text,
            "recommended_shapes": recommended_shapes,
            "count": len(products),
            "summary": summary
        }

# Hàm tiện ích để tạo node
def get_format_response_node() -> FormatResponseNode:
    """
    Tạo một instance của FormatResponseNode.
    
    Returns:
        FormatResponseNode instance
    """
    return FormatResponseNode() 