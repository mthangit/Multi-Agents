from google.adk.tools import Tool, tool
from typing import Dict, Any, List, Optional, Union
import logging
from PIL import Image
import os

from app.config.settings import SEARCH_LIMIT, DISPLAY_LIMIT
from app.models.clip_model import CLIPModelWrapper
from app.database.vector_store import VectorDatabase
from app.utils.helpers import format_results_for_display, decode_base64_to_image

logger = logging.getLogger(__name__)

clip_model = CLIPModelWrapper()
db = VectorDatabase()

class TextSearchInput:
    """Input schema cho TextSearchTool"""
    query: str
    limit: Optional[int] = SEARCH_LIMIT

class ImageSearchInput:
    """Input schema cho ImageSearchTool"""
    image_base64: str
    limit: Optional[int] = SEARCH_LIMIT

class CombinedSearchInput:
    """Input schema cho CombinedSearchTool"""
    query: Optional[str] = None
    image_base64: Optional[str] = None
    w_text: Optional[float] = 0.6
    w_image: Optional[float] = 0.4
    limit: Optional[int] = SEARCH_LIMIT

@tool("text_search", input_schema=TextSearchInput)
def text_search(query: str, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Tìm kiếm sản phẩm bằng văn bản.
    
    Args:
        query: Chuỗi văn bản truy vấn
        limit: Số lượng kết quả muốn tìm (mặc định là 5)
    
    Returns:
        Danh sách các sản phẩm liên quan nhất đến văn bản truy vấn
    """
    try:
        limit = limit or SEARCH_LIMIT
        logger.info(f"Tìm kiếm sản phẩm với văn bản: '{query}', limit={limit}")
        
        # Mã hóa văn bản thành vector
        text_vector = clip_model.encode_text(query)
        
        if not text_vector:
            return {"error": "Không thể mã hóa văn bản truy vấn", "results": []}
        
        # Tìm kiếm trong database
        results = db.search_by_text_vector(text_vector, limit=limit)
        
        # Định dạng kết quả
        formatted_results = format_results_for_display(results, query)
        
        # Thông tin hiển thị
        total = formatted_results.get("total_results", 0)
        display = formatted_results.get("displayed_results", 0)
        remaining = formatted_results.get("remaining_results", 0)
        
        if total > 0:
            message = f"Đã tìm thấy tổng cộng {total} kết quả, hiển thị {display} kết quả phù hợp nhất."
            if remaining > 0:
                message += f" Còn {remaining} kết quả khác."
            formatted_results["message"] = message
        else:
            formatted_results["message"] = "Không tìm thấy kết quả nào phù hợp với truy vấn."
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Lỗi khi tìm kiếm sản phẩm bằng văn bản: {str(e)}")
        return {
            "error": "Đã xảy ra lỗi khi tìm kiếm sản phẩm",
            "total_results": 0,
            "results": []
        }

@tool("image_search", input_schema=ImageSearchInput)
def image_search(image_base64: str, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Tìm kiếm sản phẩm bằng hình ảnh.
    
    Args:
        image_base64: Hình ảnh đã được mã hóa base64
        limit: Số lượng kết quả muốn tìm (mặc định là 5)
    
    Returns:
        Danh sách các sản phẩm liên quan nhất đến hình ảnh truy vấn
    """
    try:
        limit = limit or SEARCH_LIMIT
        logger.info(f"Tìm kiếm sản phẩm với hình ảnh, limit={limit}")
        
        # Giải mã ảnh từ chuỗi base64
        image = decode_base64_to_image(image_base64)
        
        if image is None:
            return {"error": "Không thể giải mã hình ảnh truy vấn", "results": []}
        
        # Mã hóa ảnh thành vector
        image_vector = clip_model.encode_image(image)
        
        if not image_vector:
            return {"error": "Không thể mã hóa hình ảnh truy vấn", "results": []}
        
        # Tìm kiếm trong database
        results = db.search_by_image_vector(image_vector, limit=limit)
        
        # Định dạng kết quả
        formatted_results = format_results_for_display(results)
        
        # Thông tin hiển thị
        total = formatted_results.get("total_results", 0)
        display = formatted_results.get("displayed_results", 0)
        remaining = formatted_results.get("remaining_results", 0)
        
        if total > 0:
            message = f"Đã tìm thấy tổng cộng {total} kết quả, hiển thị {display} kết quả phù hợp nhất."
            if remaining > 0:
                message += f" Còn {remaining} kết quả khác."
            formatted_results["message"] = message
        else:
            formatted_results["message"] = "Không tìm thấy kết quả nào phù hợp với hình ảnh."
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Lỗi khi tìm kiếm sản phẩm bằng hình ảnh: {str(e)}")
        return {
            "error": "Đã xảy ra lỗi khi tìm kiếm sản phẩm",
            "total_results": 0,
            "results": []
        }

@tool("combined_search", input_schema=CombinedSearchInput)
def combined_search(
    query: Optional[str] = None,
    image_base64: Optional[str] = None,
    w_text: float = 0.6, 
    w_image: float = 0.4,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Tìm kiếm sản phẩm kết hợp cả văn bản và hình ảnh.
    
    Args:
        query: Chuỗi văn bản truy vấn (tùy chọn)
        image_base64: Hình ảnh đã được mã hóa base64 (tùy chọn)
        w_text: Trọng số cho điểm text (mặc định là 0.6)
        w_image: Trọng số cho điểm ảnh (mặc định là 0.4)
        limit: Số lượng kết quả muốn tìm (mặc định là 5)
    
    Returns:
        Danh sách các sản phẩm liên quan nhất đến truy vấn kết hợp
    """
    try:
        limit = limit or SEARCH_LIMIT
        logger.info(f"Tìm kiếm sản phẩm kết hợp: text='{query}', image={'có' if image_base64 else 'không'}, limit={limit}")
        
        if not query and not image_base64:
            return {"error": "Phải cung cấp ít nhất một trong hai: văn bản hoặc hình ảnh", "results": []}
        
        # Xử lý văn bản nếu có
        text_vector = None
        if query:
            text_vector = clip_model.encode_text(query)
            
            if not text_vector:
                logger.warning("Không thể mã hóa văn bản truy vấn")
        
        # Xử lý hình ảnh nếu có
        image_vector = None
        if image_base64:
            image = decode_base64_to_image(image_base64)
            
            if image is not None:
                image_vector = clip_model.encode_image(image)
                
                if not image_vector:
                    logger.warning("Không thể mã hóa hình ảnh truy vấn")
            else:
                logger.warning("Không thể giải mã hình ảnh từ chuỗi base64")
        
        # Kiểm tra xem có vector nào không
        if not text_vector and not image_vector:
            return {"error": "Không thể xử lý cả văn bản và hình ảnh truy vấn", "results": []}
        
        # Tìm kiếm trong database
        results = db.search_combined(
            text_vector=text_vector,
            image_vector=image_vector,
            limit=limit,
            w_text=w_text,
            w_image=w_image
        )
        
        # Định dạng kết quả
        formatted_results = format_results_for_display(results, query)
        
        # Thông tin hiển thị
        total = formatted_results.get("total_results", 0)
        display = formatted_results.get("displayed_results", 0)
        remaining = formatted_results.get("remaining_results", 0)
        
        if total > 0:
            message = f"Đã tìm thấy tổng cộng {total} kết quả, hiển thị {display} kết quả phù hợp nhất."
            if remaining > 0:
                message += f" Còn {remaining} kết quả khác."
            formatted_results["message"] = message
        else:
            formatted_results["message"] = "Không tìm thấy kết quả nào phù hợp với truy vấn."
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Lỗi khi tìm kiếm sản phẩm kết hợp: {str(e)}")
        return {
            "error": "Đã xảy ra lỗi khi tìm kiếm sản phẩm",
            "total_results": 0,
            "results": []
        } 