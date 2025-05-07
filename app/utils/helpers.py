from typing import List, Dict, Any, Union, Optional
import logging
import os
from PIL import Image
import base64
import io
from app.config.settings import DISPLAY_LIMIT, SEARCH_LIMIT

logger = logging.getLogger(__name__)

def format_results_for_display(results: List[Dict[str, Any]], 
                              query: Optional[str] = None,
                              display_limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Định dạng kết quả tìm kiếm để hiển thị

    Args:
        results: Danh sách kết quả tìm kiếm
        query: Câu truy vấn tìm kiếm
        display_limit: Số lượng kết quả hiển thị

    Returns:
        Dict chứa kết quả đã định dạng
    """
    try:
        if not display_limit:
            display_limit = DISPLAY_LIMIT
        
        total_results = len(results)
        limited_results = results[:display_limit] if total_results > display_limit else results
        remaining_results = total_results - len(limited_results)
        
        # Tạo phản hồi
        response = {
            "total_results": total_results,
            "displayed_results": len(limited_results),
            "remaining_results": remaining_results,
            "results": []
        }
        
        if query:
            response["query"] = query
            
        # Định dạng từng kết quả
        for i, result in enumerate(limited_results):
            formatted_result = {
                "id": result.get("id") or f"result_{i}",
                "score": round(result.get("score", 0) * 100, 2),  # Chuyển đổi sang phần trăm và làm tròn
                "rank": i + 1
            }
            
            # Thêm thông tin từ payload nếu có
            payload = result.get("payload", {})
            
            if payload:
                # Trích xuất và thêm các trường cần thiết
                for key in ["product_id", "product_name", "category", "price", "description", "image_url", "source"]:
                    if key in payload:
                        formatted_result[key] = payload[key]
                        
                # Thêm các trường khác nếu có
                for key, value in payload.items():
                    if key not in formatted_result and key not in ["vector"]:
                        formatted_result[key] = value
            
            # Thêm thông tin về nguồn (text hoặc image)
            if "source" in result and "source" not in formatted_result:
                formatted_result["source"] = result["source"]
                
            response["results"].append(formatted_result)
            
        return response
        
    except Exception as e:
        logger.error(f"Lỗi khi định dạng kết quả: {str(e)}")
        return {
            "error": "Lỗi khi định dạng kết quả",
            "total_results": 0,
            "displayed_results": 0,
            "remaining_results": 0,
            "results": []
        }

def encode_image_to_base64(image_path: str) -> Optional[str]:
    """
    Mã hóa ảnh thành chuỗi base64

    Args:
        image_path: Đường dẫn tới file ảnh

    Returns:
        Chuỗi base64 của ảnh
    """
    try:
        if not os.path.exists(image_path):
            logger.error(f"Không tìm thấy file ảnh: {image_path}")
            return None
            
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Lỗi khi mã hóa ảnh: {str(e)}")
        return None

def decode_base64_to_image(base64_string: str) -> Optional[Image.Image]:
    """
    Giải mã chuỗi base64 thành ảnh

    Args:
        base64_string: Chuỗi base64

    Returns:
        Đối tượng PIL Image
    """
    try:
        img_data = base64.b64decode(base64_string)
        return Image.open(io.BytesIO(img_data))
    except Exception as e:
        logger.error(f"Lỗi khi giải mã ảnh: {str(e)}")
        return None

def construct_error_response(message: str, status_code: int = 500) -> Dict[str, Any]:
    """
    Tạo phản hồi lỗi tiêu chuẩn

    Args:
        message: Thông báo lỗi
        status_code: Mã trạng thái HTTP

    Returns:
        Dict chứa thông tin lỗi
    """
    return {
        "error": {
            "message": message,
            "status_code": status_code
        }
    } 