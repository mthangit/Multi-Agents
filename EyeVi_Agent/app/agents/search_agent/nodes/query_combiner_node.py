from typing import Dict, Any, Optional, List
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryCombinerNode:
    """Node kết hợp kết quả từ phân tích văn bản và hình ảnh."""
    
    def __init__(self):
        """Khởi tạo QueryCombinerNode."""
        pass
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kết hợp kết quả từ phân tích văn bản và hình ảnh.
        
        Args:
            state: Trạng thái hiện tại của workflow
            
        Returns:
            Dict chứa kết quả đã kết hợp
        """
        # Lấy các kết quả từ state
        text_normalized_query = state.get("text_normalized_query", "")
        text_extracted_attributes = state.get("text_extracted_attributes", {})
        image_normalized_query = state.get("image_normalized_query", "")
        image_extracted_attributes = state.get("image_extracted_attributes", {})
        
        # Lưu lại các giá trị quan trọng từ state ban đầu
        # has_image = state.get("has_image")
        # search_type = state.get("search_type")
        # image_data = state.get("image_data")
        # original_query = state.get("original_query", "")
        
        # Log các giá trị quan trọng
        # logger.info(f"QueryCombinerNode - has_image: {has_image}")
        # logger.info(f"QueryCombinerNode - search_type: {search_type}")
        # logger.info(f"QueryCombinerNode - image_data exists: {image_data is not None}")
        
        # Log thông tin đầu vào
        logger.info(f"Kết hợp kết quả từ text và image")
        logger.info(f"Text normalized query: {text_normalized_query}")
        # logger.info(f"Text extracted attributes: {text_extracted_attributes}")
        logger.info(f"Image normalized query: {image_normalized_query}")
        # logger.info(f"Image extracted attributes: {image_extracted_attributes}")
        
        # Kết hợp normalized query
        combined_query = self._combine_queries(text_normalized_query, image_normalized_query)
        
        # Kết hợp extracted attributes
        combined_attributes = self._combine_attributes(text_extracted_attributes, image_extracted_attributes)
        
        # Tạo kết quả với các giá trị đã kết hợp
        result = {
            "normalized_query": combined_query,
            "extracted_attributes": combined_attributes
        }
        
        # Giữ lại các giá trị quan trọng từ state ban đầu
        self._preserve_important_values(result, state)
        
        logger.info(f"Kết quả kết hợp: normalized_query={combined_query}, extracted_attributes={combined_attributes}")
        
        return result
    
    def _combine_queries(self, text_query: str, image_query: str) -> str:
        """
        Kết hợp các normalized query từ text và image.
        
        Args:
            text_query: Normalized query từ phân tích text
            image_query: Normalized query từ phân tích image
            
        Returns:
            Query đã kết hợp
        """
        # Nếu một trong hai query trống, trả về query còn lại
        if not text_query:
            return image_query
        if not image_query:
            return text_query
        
        # Nếu cả hai query giống nhau, trả về một trong hai
        if text_query.lower() == image_query.lower():
            return text_query
        
        # Nếu cả hai đều có giá trị và khác nhau, kết hợp chúng
        # Ưu tiên query từ text vì thường chính xác hơn
        combined_query = f"{text_query} {image_query}"
        
        # Loại bỏ các từ trùng lặp (đơn giản)
        words = combined_query.split()
        unique_words = []
        for word in words:
            if word.lower() not in [w.lower() for w in unique_words]:
                unique_words.append(word)
        
        return " ".join(unique_words)
    
    def _combine_attributes(self, text_attrs: Dict[str, Any], image_attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kết hợp các thuộc tính đã trích xuất từ text và image.
        
        Args:
            text_attrs: Thuộc tính từ phân tích text
            image_attrs: Thuộc tính từ phân tích image
            
        Returns:
            Thuộc tính đã kết hợp
        """
        # Nếu một trong hai thuộc tính trống, trả về thuộc tính còn lại
        if not text_attrs:
            return image_attrs
        if not image_attrs:
            return text_attrs
        
        # Kết hợp các thuộc tính, ưu tiên thuộc tính từ text
        combined_attrs = {**image_attrs, **text_attrs}
        
        return combined_attrs

    def _preserve_important_values(self, result: Dict[str, Any], state: Dict[str, Any]) -> None:
        """
        Giữ lại các giá trị quan trọng từ state ban đầu.
        
        Args:
            result: Dict kết quả sẽ được trả về
            state: Dict trạng thái ban đầu
        """
        # Danh sách các key quan trọng cần giữ lại
        important_keys = [
            "has_image", "search_type", "image_data", "original_query", 
            "text_normalized_query", "text_extracted_attributes",
            "image_normalized_query", "image_extracted_attributes",
            "image_analysis"
        ]
        
        # Giữ lại các giá trị quan trọng
        for key in important_keys:
            if key in state and state[key] is not None:
                result[key] = state[key]
        
        # logger.info(f"Đã giữ lại các giá trị quan trọng: has_image={result.get('has_image')}, search_type={result.get('search_type')}")


# Hàm tiện ích để tạo node
def get_query_combiner_node() -> QueryCombinerNode:
    """
    Tạo một instance của QueryCombinerNode.
    
    Returns:
        QueryCombinerNode instance
    """
    return QueryCombinerNode() 