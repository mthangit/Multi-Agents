import os
import logging
from typing import Dict, Any, Optional, List
import base64
from fastapi import HTTPException

from chains.search_graph import SearchChain

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchAgent:
    """
    Agent tìm kiếm sản phẩm kính mắt.
    """
    
    def __init__(self):
        """
        Khởi tạo SearchAgent.
        """
        # Lấy API key từ biến môi trường
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY không được cấu hình, một số chức năng có thể không hoạt động")
        
        # Cấu hình Qdrant
        qdrant_host = os.environ.get("QDRANT_HOST", "localhost")
        qdrant_port = int(os.environ.get("QDRANT_PORT", "6333"))
        
        # Đường dẫn đến mô hình CLIP tùy chỉnh
        custom_model_path = os.environ.get(
            "CLIP_MODEL_PATH", 
            os.path.join(os.path.dirname(__file__), "models/clip/CLIP_FTMT.pt")
        )
        
        # Khởi tạo SearchChain
        self.search_chain = SearchChain(
            api_key=api_key,
            streaming=False,  # Tắt streaming để đơn giản hóa
            qdrant_host=qdrant_host,
            qdrant_port=qdrant_port,
            custom_model_path=custom_model_path
        )
        
        logger.info("SearchAgent đã được khởi tạo thành công")
    
    async def search(
        self,
        query: Optional[str] = None,
        image_data: Optional[bytes] = None,
        analysis_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Thực hiện tìm kiếm sản phẩm.
        
        Args:
            query: Câu truy vấn tìm kiếm
            image_data: Dữ liệu hình ảnh
            analysis_result: Kết quả phân tích khuôn mặt
            
        Returns:
            Dict chứa kết quả tìm kiếm
        """
        try:
            # Kiểm tra đầu vào
            if not query and not image_data:
                raise HTTPException(
                    status_code=400, 
                    detail="Phải cung cấp ít nhất một trong hai: query hoặc image_data"
                )
            
            # Gọi SearchChain để thực hiện tìm kiếm
            result = await self.search_chain.arun(
                query=query,
                image_data=image_data,
                analysis_result=analysis_result
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Lỗi khi thực hiện tìm kiếm: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Lỗi khi thực hiện tìm kiếm: {str(e)}"
            )
    
    def search_sync(
        self,
        query: Optional[str] = None,
        image_data: Optional[bytes] = None,
        analysis_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Thực hiện tìm kiếm sản phẩm (phiên bản đồng bộ).
        
        Args:
            query: Câu truy vấn tìm kiếm
            image_data: Dữ liệu hình ảnh
            analysis_result: Kết quả phân tích khuôn mặt
            
        Returns:
            Dict chứa kết quả tìm kiếm
        """
        try:
            # Kiểm tra đầu vào
            if not query and not image_data:
                raise ValueError("Phải cung cấp ít nhất một trong hai: query hoặc image_data")
            
            # Gọi SearchChain để thực hiện tìm kiếm
            result = self.search_chain.run(
                query=query,
                image_data=image_data,
                analysis_result=analysis_result
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Lỗi khi thực hiện tìm kiếm: {e}")
            return {
                "error": str(e),
                "products": [],
                "count": 0,
                "summary": "Đã xảy ra lỗi khi tìm kiếm sản phẩm."
            }
