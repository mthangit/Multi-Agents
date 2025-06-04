from typing import Dict, Any, Optional, List
import logging
import json
import traceback
from langchain_google_genai import ChatGoogleGenerativeAI

from ..prompts.search_prompts import EXTRACT_QUERY
from ..data.filter_constants import (
    AVAILABLE_COLORS, AVAILABLE_BRANDS, AVAILABLE_FRAME_SHAPES,
    AVAILABLE_FRAME_MATERIALS, AVAILABLE_GENDERS, AVAILABLE_CATEGORIES,
    AVAILABLE_FACE_SIZES, COLOR_MAPPING, get_normalized_value
)

# Cấu hình logging chi tiết hơn
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AttributeExtractionNode:
    """Node trích xuất các thuộc tính từ query của người dùng."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Khởi tạo node trích xuất thuộc tính.
        
        Args:
            api_key: API key cho Google Generative AI
        """
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0.1,  # Nhiệt độ thấp để đảm bảo kết quả ổn định
            streaming=False   # Tắt streaming để dễ debug
        )
        logger.info("AttributeExtractionNode đã được khởi tạo")
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trích xuất các thuộc tính từ query của người dùng.
        
        Args:
            state: Trạng thái hiện tại của workflow
            
        Returns:
            Dict chứa các thuộc tính được trích xuất
        """
        # Lấy query từ state
        query = state.get("query", "")
        
        # Kiểm tra nếu query rỗng
        if not query:
            logger.warning("Query rỗng, không thể trích xuất thuộc tính")
            return {
                "extracted_attributes": {},
                "normalized_query": ""
            }
        
        try:
            # Sửa lỗi format string - Thay thế trực tiếp {query} trong prompt
            formatted_prompt = EXTRACT_QUERY.replace("{query}", query)
            
            # Gọi LLM để trích xuất thuộc tính
            response = self.llm.invoke(formatted_prompt)
            
            # Log phản hồi từ LLM
            logger.info(f"Phản hồi từ LLM:\n{response.content[:200]}...")
            
            # Phân tích kết quả JSON
            result = self._parse_extraction_result(response.content)
            
            # Log kết quả sau khi parse
            logger.info(f"Kết quả sau khi parse JSON:\n{result}")
            
            # Chuẩn hóa các giá trị thuộc tính
            normalized_attributes = self._normalize_attributes(result.get("slots", {}))
            
            logger.info(f"Đã trích xuất thuộc tính: {normalized_attributes}")
            logger.info(f"Câu mô tả chuẩn hóa: {result.get('normalized_description', query)}")
            
            # Cập nhật state với thuộc tính đã trích xuất
            return {
                "extracted_attributes": normalized_attributes,
                "normalized_query": result.get("normalized_description", query)
            }
        
        except Exception as e:
            # Log stack trace đầy đủ
            logger.error(f"Lỗi khi trích xuất thuộc tính: {e}")
            logger.error(f"Chi tiết lỗi: {traceback.format_exc()}")
            return {
                "extracted_attributes": {},
                "normalized_query": query,
                "error": str(e)
            }
    
    def _parse_extraction_result(self, result_text: str) -> Dict[str, Any]:
        """
        Phân tích kết quả trích xuất từ LLM.
        
        Args:
            result_text: Kết quả trả về từ LLM
            
        Returns:
            Dict chứa các thuộc tính đã được phân tích
        """
        try:
            # Tìm JSON trong kết quả
            start_idx = result_text.find('{')
            end_idx = result_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = result_text[start_idx:end_idx]
                logger.debug(f"Chuỗi JSON được trích xuất: {json_str}")
                parsed_result = json.loads(json_str)
                return parsed_result
            else:
                logger.warning(f"Không tìm thấy JSON trong kết quả trích xuất: {result_text}")
                return {
                    "normalized_description": "",
                    "slots": {}
                }
        except json.JSONDecodeError as e:
            logger.error(f"Lỗi khi phân tích JSON: {e}")
            logger.error(f"Chuỗi JSON gây lỗi: {result_text}")
            # Thử tìm và sửa JSON không hợp lệ
            try:
                # Thử thay thế các ký tự có thể gây lỗi
                fixed_json = result_text.replace("'", '"').replace('\n', ' ')
                start_idx = fixed_json.find('{')
                end_idx = fixed_json.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    fixed_json_str = fixed_json[start_idx:end_idx]
                    logger.info(f"Thử phân tích JSON đã sửa: {fixed_json_str}")
                    return json.loads(fixed_json_str)
            except:
                logger.error("Không thể sửa JSON")
            
            return {
                "normalized_description": "",
                "slots": {}
            }
    
    def _normalize_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Chuẩn hóa các giá trị thuộc tính.
        
        Args:
            attributes: Dict chứa các thuộc tính cần chuẩn hóa
            
        Returns:
            Dict chứa các thuộc tính đã được chuẩn hóa
        """
        try:
            normalized = {}
            logger.debug(f"Chuẩn hóa thuộc tính: {attributes}")
            
            # Chuẩn hóa category
            if "category" in attributes and attributes["category"]:
                category_value = attributes["category"]
                logger.debug(f"Giá trị category trước khi chuẩn hóa: {category_value}")
                
                # Xử lý đặc biệt cho category
                if category_value == "Kính Mát/Gọng Kính":
                    # Mặc định chọn "Kính Mát"
                    normalized["category"] = "Kính Mát"
                    logger.info(f"Đã xử lý giá trị đặc biệt '{category_value}' thành 'Kính Mát'")
                else:
                    normalized["category"] = category_value
            
            # Chuẩn hóa brand
            if "brand" in attributes and attributes["brand"]:
                normalized["brand"] = attributes["brand"]
            
            # Chuẩn hóa gender
            if "gender" in attributes and attributes["gender"]:
                normalized["gender"] = attributes["gender"]
            
            # Chuẩn hóa color
            if "color" in attributes and attributes["color"]:
                normalized["color"] = attributes["color"]
            
            # Chuẩn hóa frame material
            if "frameMaterial" in attributes and attributes["frameMaterial"]:
                normalized["frame_material"] = attributes["frameMaterial"]
            
            # Chuẩn hóa frame shape
            if "frameShape" in attributes and attributes["frameShape"]:
                shape = attributes["frameShape"]
                if shape:
                    normalized["recommended_shapes"] = [shape]
            
            return normalized
            
        except Exception as e:
            logger.error(f"Lỗi khi chuẩn hóa thuộc tính: {e}")
            logger.error(traceback.format_exc())
            return {}

# Hàm tiện ích để tạo node
def get_attribute_extraction_node(api_key: Optional[str] = None) -> AttributeExtractionNode:
    """
    Tạo một instance của AttributeExtractionNode.
    
    Args:
        api_key: API key cho Google Generative AI
        
    Returns:
        AttributeExtractionNode instance
    """
    return AttributeExtractionNode(api_key=api_key) 