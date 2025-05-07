from typing import Dict, Any, List, Optional, Union
from app.tools.base_tool import BaseTool
from app.database.vector_store import VectorDatabase
from app.models.clip_model import CLIPModelWrapper
from app.config.settings import Settings

class GlassesSearchTool(BaseTool):
    """Tool tìm kiếm kính mắt trong vector database sử dụng CLIP model"""
    
    def __init__(self):
        super().__init__(
            name="glasses_search",
            description="Tìm kiếm kính mắt dựa trên mô tả hoặc hình ảnh sử dụng CLIP model"
        )
        self.vector_db = VectorDatabase()
        self.clip_model = CLIPModelWrapper()
        self.default_limit = 5
        
    async def execute(self,
                     query: Optional[str] = None,
                     image_url: Optional[str] = None,
                     limit: int = None,
                     filter_params: Dict = None,
                     w_image: float = 0.4,
                     w_text: float = 0.6) -> Dict[str, Any]:
        """Thực hiện tìm kiếm kính mắt"""
        try:
            limit = limit or self.default_limit
            product_scores = {}
            product_details = {}
            
            if image_url:
                # Lấy vector từ ảnh
                image_vector = self.clip_model.encode_image(image_url)
                if image_vector is not None:
                    # Tìm kiếm trong vector database
                    image_results = await self.vector_db.search_by_image_vector(
                        vector=image_vector,
                        limit=limit * 3,
                        filter_params=filter_params
                    )
                    
                    # Cộng điểm từ kết quả ảnh (có trọng số)
                    for result in image_results:
                        product_id = result["product_id"]
                        product_scores[product_id] = result["score"] * w_image
                        product_details[product_id] = result
            
            if query:
                # Lấy vector từ text
                text_vector = self.clip_model.encode_text(query)
                if text_vector is not None:
                    # Tìm kiếm trong vector database
                    text_results = await self.vector_db.search_by_text_vector(
                        vector=text_vector,
                        limit=limit * 3,
                        filter_params=filter_params
                    )
                    
                    # Cộng điểm từ kết quả text (có trọng số)
                    for result in text_results:
                        product_id = result["product_id"]
                        if product_id in product_scores:
                            product_scores[product_id] += result["score"] * w_text
                        else:
                            product_scores[product_id] = result["score"] * w_text
                        if product_id not in product_details:
                            product_details[product_id] = result
            
            # Sắp xếp kết quả theo tổng điểm
            sorted_results = sorted(
                [
                    {
                        "product_id": product_id,
                        "score": score,
                        **product_details[product_id]
                    }
                    for product_id, score in product_scores.items()
                ],
                key=lambda x: x["score"],
                reverse=True
            )
            
            # Trả về top k kết quả
            return {
                "status": "success",
                "results": sorted_results[:limit],
                "total": len(sorted_results),
                "offset": 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            } 