from typing import List, Optional
from pydantic import BaseModel, Field


class Product(BaseModel):
    """Model cho sản phẩm kính mắt."""
    
    product_id: str = Field(..., description="ID duy nhất của sản phẩm")
    name: str = Field(..., description="Tên sản phẩm")
    brand: str = Field(..., description="Thương hiệu")
    price: float = Field(..., description="Giá sản phẩm (VND)")
    description: Optional[str] = Field(None, description="Mô tả sản phẩm")
    image_url: Optional[str] = Field(None, description="URL hình ảnh sản phẩm")
    
    # Thông tin về gọng kính
    frame_shape: Optional[str] = Field(None, description="Hình dạng gọng kính (e.g., rectangle, square, round, oval)")
    frame_color: Optional[str] = Field(None, description="Màu sắc gọng kính")
    frame_material: Optional[str] = Field(None, description="Chất liệu gọng kính")
    
    # Thông tin về lọc
    gender: Optional[str] = Field(None, description="Giới tính (men, women, unisex)")
    style: Optional[str] = Field(None, description="Phong cách (e.g., classic, modern, sporty)")
    
    # Thông tin kỹ thuật
    lens_width: Optional[float] = Field(None, description="Chiều rộng tròng kính (mm)")
    bridge_width: Optional[float] = Field(None, description="Chiều rộng cầu mũi (mm)")
    temple_length: Optional[float] = Field(None, description="Chiều dài càng kính (mm)")
    
    # Metadata
    tags: Optional[List[str]] = Field(None, description="Các tag liên quan")
    score: Optional[float] = Field(None, description="Điểm tương đồng trong tìm kiếm")


class SearchQuery(BaseModel):
    """Model cho query tìm kiếm."""
    
    query_text: Optional[str] = Field(None, description="Văn bản tìm kiếm")
    image_data: Optional[bytes] = Field(None, description="Dữ liệu ảnh để tìm kiếm")
    face_shape: Optional[str] = Field(None, description="Hình dạng khuôn mặt người dùng")
    recommended_shapes: Optional[List[str]] = Field(None, description="Các hình dạng gọng kính được đề xuất")
    filter_params: Optional[dict] = Field(None, description="Các tham số lọc bổ sung")
    limit: Optional[int] = Field(5, description="Số lượng kết quả trả về")


class ImageAnalysisResult(BaseModel):
    """Model cho kết quả phân tích ảnh."""
    
    face_detected: bool = Field(..., description="Có phát hiện khuôn mặt không")
    glasses_detected: Optional[bool] = Field(False, description="Có phát hiện kính không")
    skin_tone: Optional[str] = Field(None, description="Tông màu da (light, medium, dark)")
    face_shape: Optional[str] = Field(None, description="Hình dạng khuôn mặt")
    recommended_frame_shapes: Optional[List[str]] = Field(None, description="Các hình dạng gọng kính được đề xuất")
    glasses_observed: Optional[dict] = Field(None, description="Thông tin về kính đang đeo (nếu có)")
    summary: Optional[str] = Field(None, description="Tóm tắt kết quả phân tích")


class SearchResults(BaseModel):
    """Model cho kết quả tìm kiếm."""
    
    products: List[Product] = Field(..., description="Danh sách sản phẩm tìm thấy")
    query: Optional[str] = Field(None, description="Query văn bản gốc")
    recommended_shapes: Optional[List[str]] = Field(None, description="Các hình dạng gọng kính được đề xuất")
    count: int = Field(..., description="Số lượng sản phẩm tìm thấy")
    summary: str = Field(..., description="Tóm tắt kết quả tìm kiếm")


class SearchResponse(BaseModel):
    """Model cho phản hồi từ search agent."""
    
    results: SearchResults = Field(..., description="Kết quả tìm kiếm")
    analysis: Optional[ImageAnalysisResult] = Field(None, description="Kết quả phân tích ảnh (nếu có)")
    message: Optional[str] = Field(None, description="Thông báo bổ sung")
