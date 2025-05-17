import io
import os
import torch
from typing import List, Dict, Optional, Union
from PIL import Image

from langchain.tools import tool
from pydantic import BaseModel, Field

from ..search_service import ProductSearch
from ..models.product import ImageAnalysisResult


# Đường dẫn đến mô hình fine-tuned (có thể đưa vào biến môi trường)
custom_model_path = os.environ.get(
    "CLIP_MODEL_PATH", 
    os.path.join(os.path.dirname(__file__), "../models/clip/CLIP_FTMT.pt")
)

# Báo cáo thông tin về mô hình tùy chỉnh
if os.path.exists(custom_model_path):
    print(f"Đã tìm thấy mô hình tùy chỉnh tại: {custom_model_path}")
else:
    print(f"Không tìm thấy mô hình tùy chỉnh tại: {custom_model_path}")
    print(f"Sẽ sử dụng mô hình mặc định")

# Khởi tạo đối tượng ProductSearch với mô hình tùy chỉnh
product_search = ProductSearch(
    qdrant_host=os.environ.get("QDRANT_HOST", "localhost"),
    qdrant_port=int(os.environ.get("QDRANT_PORT", "6333")),
    custom_model_path=custom_model_path if os.path.exists(custom_model_path) else None
)


class TextSearchInput(BaseModel):
    """Input cho công cụ tìm kiếm bằng văn bản."""
    query: str = Field(..., description="Câu truy vấn tìm kiếm")
    limit: Optional[int] = Field(5, description="Số lượng kết quả trả về")
    frame_shape: Optional[str] = Field(None, description="Lọc theo hình dạng gọng kính")
    brand: Optional[str] = Field(None, description="Lọc theo thương hiệu")
    color: Optional[str] = Field(None, description="Lọc theo màu sắc")
    gender: Optional[str] = Field(None, description="Lọc theo giới tính (men, women, unisex)")
    min_price: Optional[float] = Field(None, description="Giá tối thiểu")
    max_price: Optional[float] = Field(None, description="Giá tối đa")
    style: Optional[str] = Field(None, description="Phong cách kính")
    recommended_shapes: Optional[List[str]] = Field(None, description="Các hình dạng gọng kính được đề xuất từ phân tích khuôn mặt")


class ImageSearchInput(BaseModel):
    """Input cho công cụ tìm kiếm bằng hình ảnh."""
    image_url: Optional[str] = Field(None, description="URL hình ảnh để tìm kiếm")
    limit: Optional[int] = Field(5, description="Số lượng kết quả trả về")
    frame_shape: Optional[str] = Field(None, description="Lọc theo hình dạng gọng kính")
    brand: Optional[str] = Field(None, description="Lọc theo thương hiệu")
    color: Optional[str] = Field(None, description="Lọc theo màu sắc")
    gender: Optional[str] = Field(None, description="Lọc theo giới tính (men, women, unisex)")
    min_price: Optional[float] = Field(None, description="Giá tối thiểu")
    max_price: Optional[float] = Field(None, description="Giá tối đa")
    style: Optional[str] = Field(None, description="Phong cách kính")
    recommended_shapes: Optional[List[str]] = Field(None, description="Các hình dạng gọng kính được đề xuất từ phân tích khuôn mặt")


class CombinedSearchInput(BaseModel):
    """Input cho công cụ tìm kiếm kết hợp văn bản và hình ảnh."""
    query: Optional[str] = Field(None, description="Câu truy vấn tìm kiếm văn bản")
    image_url: Optional[str] = Field(None, description="URL hình ảnh để tìm kiếm")
    limit: Optional[int] = Field(5, description="Số lượng kết quả trả về")
    frame_shape: Optional[str] = Field(None, description="Lọc theo hình dạng gọng kính")
    brand: Optional[str] = Field(None, description="Lọc theo thương hiệu")
    color: Optional[str] = Field(None, description="Lọc theo màu sắc")
    gender: Optional[str] = Field(None, description="Lọc theo giới tính (men, women, unisex)")
    min_price: Optional[float] = Field(None, description="Giá tối thiểu")
    max_price: Optional[float] = Field(None, description="Giá tối đa")
    style: Optional[str] = Field(None, description="Phong cách kính")
    w_image: Optional[float] = Field(0.4, description="Trọng số cho điểm ảnh")
    w_text: Optional[float] = Field(0.6, description="Trọng số cho điểm văn bản")
    recommended_shapes: Optional[List[str]] = Field(None, description="Các hình dạng gọng kính được đề xuất từ phân tích khuôn mặt")


def _create_filter_params(input_model: Union[TextSearchInput, ImageSearchInput, CombinedSearchInput]) -> Dict:
    """Tạo filter_params từ input."""
    filter_params = {}
    
    if hasattr(input_model, 'frame_shape') and input_model.frame_shape:
        filter_params['frame_shape'] = input_model.frame_shape
    
    if hasattr(input_model, 'brand') and input_model.brand:
        filter_params['brand'] = input_model.brand
    
    if hasattr(input_model, 'color') and input_model.color:
        filter_params['frame_color'] = input_model.color
    
    if hasattr(input_model, 'gender') and input_model.gender:
        filter_params['gender'] = input_model.gender
    
    if hasattr(input_model, 'style') and input_model.style:
        filter_params['style'] = input_model.style
        
    # Các filter khác như price_range có thể được thêm sau
    
    return filter_params


@tool("search_by_text", args_schema=TextSearchInput)
def search_by_text(
    query: str,
    limit: int = 5,
    frame_shape: Optional[str] = None,
    brand: Optional[str] = None,
    color: Optional[str] = None, 
    gender: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    style: Optional[str] = None,
    recommended_shapes: Optional[List[str]] = None
) -> Dict:
    """
    Tìm kiếm sản phẩm kính mắt bằng văn bản.
    
    Sử dụng tool này khi bạn cần tìm kiếm sản phẩm kính mắt dựa trên mô tả văn bản.
    Bạn có thể lọc kết quả theo hình dạng gọng kính, thương hiệu, màu sắc và nhiều tiêu chí khác.
    """
    input_obj = TextSearchInput(
        query=query,
        limit=limit,
        frame_shape=frame_shape,
        brand=brand,
        color=color,
        gender=gender,
        min_price=min_price,
        max_price=max_price,
        style=style,
        recommended_shapes=recommended_shapes
    )
    
    filter_params = _create_filter_params(input_obj)
    results = product_search.search_by_text(query, limit=limit, filter_params=filter_params)
    
    return product_search.format_search_results(
        results=results,
        query_text=query,
        recommended_shapes=recommended_shapes
    )


@tool("search_by_image", args_schema=ImageSearchInput)
def search_by_image(
    image_url: str,
    limit: int = 5,
    frame_shape: Optional[str] = None,
    brand: Optional[str] = None,
    color: Optional[str] = None,
    gender: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    style: Optional[str] = None,
    recommended_shapes: Optional[List[str]] = None
) -> Dict:
    """
    Tìm kiếm sản phẩm kính mắt dựa trên hình ảnh.
    
    Sử dụng tool này khi bạn cần tìm kiếm sản phẩm kính mắt dựa trên một hình ảnh.
    Hình ảnh có thể là kính mắt hoặc khuôn mặt người dùng.
    Bạn có thể lọc kết quả theo hình dạng gọng kính, thương hiệu, màu sắc và nhiều tiêu chí khác.
    """
    input_obj = ImageSearchInput(
        image_url=image_url,
        limit=limit,
        frame_shape=frame_shape,
        brand=brand,
        color=color,
        gender=gender,
        min_price=min_price,
        max_price=max_price,
        style=style,
        recommended_shapes=recommended_shapes
    )
    
    filter_params = _create_filter_params(input_obj)
    results = product_search.search_by_image(image_url, limit=limit, filter_params=filter_params)
    
    return product_search.format_search_results(
        results=results,
        recommended_shapes=recommended_shapes
    )


@tool("search_combined", args_schema=CombinedSearchInput)
def search_combined(
    query: Optional[str] = None,
    image_url: Optional[str] = None,
    limit: int = 5,
    frame_shape: Optional[str] = None,
    brand: Optional[str] = None,
    color: Optional[str] = None,
    gender: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    style: Optional[str] = None,
    w_image: float = 0.4,
    w_text: float = 0.6,
    recommended_shapes: Optional[List[str]] = None
) -> Dict:
    """
    Tìm kiếm sản phẩm kính mắt kết hợp cả văn bản và hình ảnh.
    
    Sử dụng tool này khi bạn cần tìm kiếm bằng cả văn bản và hình ảnh đồng thời.
    Bạn có thể điều chỉnh trọng số giữa kết quả tìm kiếm từ văn bản và từ hình ảnh.
    """
    input_obj = CombinedSearchInput(
        query=query,
        image_url=image_url,
        limit=limit,
        frame_shape=frame_shape,
        brand=brand,
        color=color,
        gender=gender,
        min_price=min_price,
        max_price=max_price,
        style=style,
        w_image=w_image,
        w_text=w_text,
        recommended_shapes=recommended_shapes
    )
    
    filter_params = _create_filter_params(input_obj)
    
    if not query and not image_url:
        return {"error": "Phải cung cấp ít nhất query văn bản hoặc URL hình ảnh"}
    
    results = product_search.search_combined(
        text=query, 
        image=image_url if image_url else None,
        limit=limit,
        filter_params=filter_params,
        w_image=w_image,
        w_text=w_text
    )
    
    return product_search.format_search_results(
        results=results,
        query_text=query,
        recommended_shapes=recommended_shapes
    )


@tool("parse_face_analysis")
def parse_face_analysis(analysis_result: Dict) -> ImageAnalysisResult:
    """
    Phân tích kết quả của việc phân tích khuôn mặt từ host agent.
    
    Sử dụng tool này để chuyển đổi kết quả phân tích từ host agent thành định dạng
    phù hợp cho việc tìm kiếm sản phẩm.
    """
    try:
        # Validate và chuyển đổi sang ImageAnalysisResult
        result = ImageAnalysisResult(
            face_detected=analysis_result.get("face_detected", False),
            glasses_detected=analysis_result.get("glasses_detected", False),
            skin_tone=analysis_result.get("skin_tone"),
            face_shape=analysis_result.get("face_shape"),
            recommended_frame_shapes=analysis_result.get("recommended_frame_shapes", []),
            glasses_observed=analysis_result.get("glasses_observed", {}),
            summary=analysis_result.get("summary", "")
        )
        return result
    except Exception as e:
        return {"error": f"Lỗi khi phân tích kết quả: {str(e)}"}


def get_search_tools():
    """Trả về danh sách các tool tìm kiếm."""
    return [
        search_by_text,
        search_by_image,
        search_combined,
        parse_face_analysis
    ]
