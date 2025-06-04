# import io
# import os
# import types
# import torch
# from typing import List, Dict, Optional, Union
# from PIL import Image

# from langchain.tools import tool
# from pydantic import BaseModel, Field

# from ..search_service import ProductSearch
# from ..models.product import ImageAnalysisResult
# from ..data.filter_constants import (
#     COLOR_MAPPING,
#     AVAILABLE_COLORS, AVAILABLE_BRANDS,
#     AVAILABLE_FRAME_SHAPES,
#     AVAILABLE_FRAME_MATERIALS,
#     AVAILABLE_GENDERS,
#     AVAILABLE_CATEGORIES,
#     AVAILABLE_FACE_SIZES,
#     get_normalized_value
# )


# # Đường dẫn đến mô hình fine-tuned (có thể đưa vào biến môi trường)
# custom_model_path = os.environ.get(
#     "CLIP_MODEL_PATH", 
#     os.path.join(os.path.dirname(__file__), "../models/clip/CLIP_FTMT.pt")
# )

# # Báo cáo thông tin về mô hình tùy chỉnh
# if os.path.exists(custom_model_path):
#     print(f"Đã tìm thấy mô hình tùy chỉnh tại: {custom_model_path}")
# else:
#     print(f"Không tìm thấy mô hình tùy chỉnh tại: {custom_model_path}")
#     print(f"Sẽ sử dụng mô hình mặc định")

# # Khởi tạo đối tượng ProductSearch với mô hình tùy chỉnh
# product_search = ProductSearch(
#     qdrant_host="localhost",
#     qdrant_port=int(os.environ.get("QDRANT_PORT", "6333")),
#     # custom_model_path=None,
#     custom_model_path=custom_model_path if os.path.exists(custom_model_path) else None
# )


# class TextSearchInput(BaseModel):
#     """Input cho công cụ tìm kiếm bằng văn bản."""
#     query: str = Field(..., description="Câu truy vấn tìm kiếm")
#     limit: Optional[int] = Field(5, description="Số lượng kết quả trả về")
#     brand: Optional[str] = Field(None, description="Lọc theo thương hiệu")
#     color: Optional[str] = Field(None, description="Lọc theo màu sắc")
#     gender: Optional[str] = Field(None, description="Lọc theo giới tính (men, women, unisex)")
#     style: Optional[str] = Field(None, description="Phong cách kính (có thể dùng để lọc theo chất liệu)")
#     frame_material: Optional[str] = Field(None, description="Chất liệu gọng kính")
#     face_size: Optional[str] = Field(None, description="Kích thước khuôn mặt phù hợp (Mặt nhỏ, Mặt trung bình, Mặt to)")
#     lens_width: Optional[int] = Field(None, description="Chiều rộng tròng kính (mm)")
#     category: Optional[str] = Field(None, description="Danh mục sản phẩm (Kính Mát, Gọng kính)")
#     recommended_shapes: Optional[List[str]] = Field(None, description="Các hình dạng gọng kính được đề xuất từ phân tích khuôn mặt")


# class ImageSearchInput(BaseModel):
#     """Input cho công cụ tìm kiếm bằng hình ảnh."""
#     image_url: Optional[str] = Field(None, description="URL hình ảnh để tìm kiếm")
#     limit: Optional[int] = Field(5, description="Số lượng kết quả trả về")
#     brand: Optional[str] = Field(None, description="Lọc theo thương hiệu")
#     color: Optional[str] = Field(None, description="Lọc theo màu sắc")
#     gender: Optional[str] = Field(None, description="Lọc theo giới tính (men, women, unisex)")
#     style: Optional[str] = Field(None, description="Phong cách kính")
#     frame_material: Optional[str] = Field(None, description="Chất liệu gọng kính")
#     face_size: Optional[str] = Field(None, description="Kích thước khuôn mặt phù hợp")
#     lens_width: Optional[int] = Field(None, description="Chiều rộng tròng kính (mm)")
#     category: Optional[str] = Field(None, description="Danh mục sản phẩm (Kính Mát, Gọng kính)")
#     recommended_shapes: Optional[List[str]] = Field(None, description="Các hình dạng gọng kính được đề xuất từ phân tích khuôn mặt")


# class CombinedSearchInput(BaseModel):
#     """Input cho công cụ tìm kiếm kết hợp văn bản và hình ảnh."""
#     query: Optional[str] = Field(None, description="Câu truy vấn tìm kiếm văn bản")
#     image_url: Optional[str] = Field(None, description="URL hình ảnh để tìm kiếm")
#     limit: Optional[int] = Field(5, description="Số lượng kết quả trả về")
#     brand: Optional[str] = Field(None, description="Lọc theo thương hiệu")
#     color: Optional[str] = Field(None, description="Lọc theo màu sắc")
#     gender: Optional[str] = Field(None, description="Lọc theo giới tính (men, women, unisex)")
#     style: Optional[str] = Field(None, description="Phong cách kính")
#     frame_material: Optional[str] = Field(None, description="Chất liệu gọng kính")
#     face_size: Optional[str] = Field(None, description="Kích thước khuôn mặt phù hợp")
#     lens_width: Optional[int] = Field(None, description="Chiều rộng tròng kính (mm)")
#     category: Optional[str] = Field(None, description="Danh mục sản phẩm (Kính Mát, Gọng kính)")
#     w_image: Optional[float] = Field(0.4, description="Trọng số cho điểm ảnh")
#     w_text: Optional[float] = Field(0.6, description="Trọng số cho điểm văn bản")
#     recommended_shapes: Optional[List[str]] = Field(None, description="Các hình dạng gọng kính được đề xuất từ phân tích khuôn mặt")

# @tool("search_by_text", args_schema=TextSearchInput)
# def search_by_text(
#     query: str,
#     limit: int = 5,
#     brand: Optional[str] = None,
#     color: Optional[str] = None, 
#     gender: Optional[str] = None,
#     style: Optional[str] = None,
#     frame_material: Optional[str] = None,
#     face_size: Optional[str] = None,
#     lens_width: Optional[int] = None,
#     category: Optional[str] = None,
#     min_price: Optional[int] = None,
#     max_price: Optional[int] = None,
#     recommended_shapes: Optional[List[str]] = None
# ) -> Dict:
#     """
#     Tìm kiếm sản phẩm kính mắt bằng văn bản.
    
#     Sử dụng tool này khi bạn cần tìm kiếm sản phẩm kính mắt dựa trên mô tả văn bản.
#     Bạn có thể lọc kết quả theo hình dạng gọng kính, thương hiệu, màu sắc và nhiều tiêu chí khác.
#     """

#     input_obj = TextSearchInput(
#         query=query,
#         limit=limit,
#         brand=brand,
#         color=color,
#         gender=gender,
#         style=style,
#         frame_material=frame_material,
#         face_size=face_size,
#         lens_width=lens_width,
#         category=category,
#         min_price=min_price,
#         max_price=max_price,
#         recommended_shapes=recommended_shapes
#     )


#     # Lấy kết quả từ search_service và tiêu thụ generator ngay lập tức
#     result_data = list(product_search.search_by_text(
#         query, limit=limit, filter_params=None, streaming=True
#     ))
    
#     print("results in tool (kiểu dữ liệu): ", type(result_data))
#     print("results in tool (số lượng): ", len(result_data))
#     print("results in tool (nội dung): ", result_data[:3] if result_data else [])

#     formatted_results = product_search.format_search_results(
#         results=result_data,
#         query_text=query,
#         recommended_shapes=recommended_shapes
#     )
    
#     return formatted_results


# @tool("search_by_image", args_schema=ImageSearchInput)
# def search_by_image(
#     image_url: str,
#     limit: int = 5,
#     brand: Optional[str] = None,
#     color: Optional[str] = None,
#     gender: Optional[str] = None,
#     style: Optional[str] = None,
#     frame_material: Optional[str] = None,
#     face_size: Optional[str] = None,
#     lens_width: Optional[int] = None,
#     category: Optional[str] = None,
#     min_price: Optional[int] = None,
#     max_price: Optional[int] = None,
#     recommended_shapes: Optional[List[str]] = None
# ) -> Dict:
#     """
#     Tìm kiếm sản phẩm kính mắt dựa trên hình ảnh.
    
#     Sử dụng tool này khi bạn cần tìm kiếm sản phẩm kính mắt dựa trên một hình ảnh.
#     Hình ảnh có thể là kính mắt hoặc khuôn mặt người dùng.
#     Bạn có thể lọc kết quả theo hình dạng gọng kính, thương hiệu, màu sắc và nhiều tiêu chí khác.
#     """
#     input_obj = ImageSearchInput(
#         image_url=image_url,
#         limit=limit,
#         brand=brand,
#         color=color,
#         gender=gender,
#         style=style,
#         frame_material=frame_material,
#         face_size=face_size,
#         lens_width=lens_width,
#         category=category,
#         min_price=min_price,
#         max_price=max_price,
#         recommended_shapes=recommended_shapes
#     )
    
#     filter_params = _create_filter_params(input_obj)
    
#     # Debug thông tin filter
#     print(f"Filter params: {filter_params}")
    
#     # Chuyển đổi kết quả thành list để tránh vấn đề generator
#     results = list(product_search.search_by_image(
#         image_url, limit=limit, filter_params=filter_params, streaming=True
#     ))
    
#     return product_search.format_search_results(
#         results=results,
#         recommended_shapes=recommended_shapes
#     )


# @tool("search_combined", args_schema=CombinedSearchInput)
# def search_combined(
#     query: Optional[str] = None,
#     image_url: Optional[str] = None,
#     limit: int = 5,
#     brand: Optional[str] = None,
#     color: Optional[str] = None,
#     gender: Optional[str] = None,
#     style: Optional[str] = None,
#     frame_material: Optional[str] = None,
#     face_size: Optional[str] = None,
#     lens_width: Optional[int] = None,
#     category: Optional[str] = None,
#     min_price: Optional[int] = None,
#     max_price: Optional[int] = None,
#     w_image: float = 0.4,
#     w_text: float = 0.6,
#     recommended_shapes: Optional[List[str]] = None
# ) -> Dict:
#     """
#     Tìm kiếm sản phẩm kính mắt kết hợp cả văn bản và hình ảnh.
    
#     Sử dụng tool này khi bạn cần tìm kiếm bằng cả văn bản và hình ảnh đồng thời.
#     Bạn có thể điều chỉnh trọng số giữa kết quả tìm kiếm từ văn bản và từ hình ảnh.
#     """
#     input_obj = CombinedSearchInput(
#         query=query,
#         image_url=image_url,
#         limit=limit,
#         brand=brand,
#         color=color,
#         gender=gender,
#         style=style,
#         frame_material=frame_material,
#         face_size=face_size,
#         lens_width=lens_width,
#         category=category,
#         min_price=min_price,
#         max_price=max_price,
#         w_image=w_image,
#         w_text=w_text,
#         recommended_shapes=recommended_shapes
#     )
    
#     filter_params = _create_filter_params(input_obj)
    
#     # Debug thông tin filter
#     print(f"Filter params: {filter_params}")
    
#     if not query and not image_url:
#         return {"error": "Phải cung cấp ít nhất query văn bản hoặc URL hình ảnh"}
    
#     # Chuyển đổi kết quả thành list để tránh vấn đề generator
#     results = list(product_search.search_combined(
#         text=query, 
#         image=image_url if image_url else None,
#         limit=limit,
#         filter_params=filter_params,
#         w_image=w_image,
#         w_text=w_text,
#         streaming=True
#     ))
    
#     return product_search.format_search_results(
#         results=results,
#         query_text=query,
#         recommended_shapes=recommended_shapes
#     )


# @tool("parse_face_analysis")
# def parse_face_analysis(analysis_result: Dict) -> ImageAnalysisResult:
#     """
#     Phân tích kết quả của việc phân tích khuôn mặt từ host agent.
    
#     Sử dụng tool này để chuyển đổi kết quả phân tích từ host agent thành định dạng
#     phù hợp cho việc tìm kiếm sản phẩm.
#     """
#     try:
#         # Validate và chuyển đổi sang ImageAnalysisResult
#         result = ImageAnalysisResult(
#             face_detected=analysis_result.get("face_detected", False),
#             glasses_detected=analysis_result.get("glasses_detected", False),
#             skin_tone=analysis_result.get("skin_tone"),
#             face_shape=analysis_result.get("face_shape"),
#             recommended_frame_shapes=analysis_result.get("recommended_frame_shapes", []),
#             glasses_observed=analysis_result.get("glasses_observed", {}),
#             summary=analysis_result.get("summary", "")
#         )
#         return result
#     except Exception as e:
#         return {"error": f"Lỗi khi phân tích kết quả: {str(e)}"}


# def get_search_tools():
#     """Trả về danh sách các tool tìm kiếm."""
#     return [
#         search_by_text,
#         search_by_image,
#         search_combined,
#         parse_face_analysis
#     ]
