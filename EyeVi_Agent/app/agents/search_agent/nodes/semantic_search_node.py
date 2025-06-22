from typing import Dict, Any, Optional, List, Union
import logging
import traceback
import json

from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from data.filter_constants import (AVAILABLE_BRANDS)

# Cấu hình logging chi tiết hơn
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SemanticSearchNode:
    """Node thực hiện tìm kiếm ngữ nghĩa trên Qdrant."""
    
    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        default_limit: int = 5
    ):
        """
        Khởi tạo node tìm kiếm ngữ nghĩa.
        
        Args:
            qdrant_host: Host của Qdrant server
            qdrant_port: Port của Qdrant server
            default_limit: Số lượng kết quả mặc định trả về
        """
        try:
            self.qdrant_client = QdrantClient("http://eyevi.devsecopstech.click", port=qdrant_port)
            logger.info(f"Đã kết nối đến Qdrant tại {"http://eyevi.devsecopstech.click"}:{qdrant_port}")
        except Exception as e:
            logger.error(f"Lỗi khi kết nối đến Qdrant: {e}")
            raise
        
        self.default_limit = default_limit
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Thực hiện tìm kiếm ngữ nghĩa trên Qdrant.
        
        Args:
            state: Trạng thái hiện tại của workflow
            
        Returns:
            Dict chứa kết quả tìm kiếm
        """
        # Lấy thông tin từ state
        search_type = state.get("search_type")
        text_embedding = state.get("text_embedding")
        image_embedding = state.get("image_embedding")
        extracted_attributes = state.get("extracted_attributes", {})
        normalized_query = state.get("normalized_query", "")
        
        # Log thông tin tìm kiếm
        logger.info(f"Thực hiện tìm kiếm loại: {search_type}")
        logger.info(f"Query chuẩn hóa: {normalized_query}")
        logger.info(f"Thuộc tính đã trích xuất: {extracted_attributes}")
        
        # Kiểm tra và điều chỉnh search_type nếu cần
        # Nếu search_type là combined nhưng không có text_embedding, chuyển thành image
        if search_type == "combined" and not text_embedding:
            logger.info("Điều chỉnh search_type từ 'combined' thành 'image' vì không có text_embedding")
            search_type = "image"
            state["search_type"] = "image"
            
        # Nếu search_type là combined nhưng không có image_embedding, chuyển thành text
        elif search_type == "combined" and not image_embedding:
            logger.info("Điều chỉnh search_type từ 'combined' thành 'text' vì không có image_embedding")
            search_type = "text"
            state["search_type"] = "text"
        
        # Số lượng kết quả trả về
        limit = state.get("limit", self.default_limit)
        
        # Tạo filter từ extracted_attributes
        filter_params = self._create_filter_params(extracted_attributes)
        if filter_params:
            logger.info(f"Áp dụng filter: {filter_params}")
        
        try:
            # Thực hiện tìm kiếm theo loại
            if search_type == "text" and text_embedding:
                logger.info("Thực hiện tìm kiếm bằng text embedding")
                results = self._search_by_text(text_embedding, limit, filter_params)
            elif search_type == "image" and image_embedding:
                logger.info("Thực hiện tìm kiếm bằng image embedding")
                results = self._search_by_image(image_embedding, limit, filter_params)
            elif search_type == "combined" and text_embedding and image_embedding:
                logger.info("Thực hiện tìm kiếm kết hợp text và image embedding")
                results = self._search_combined(
                    text_embedding, image_embedding, limit, filter_params
                )
            else:
                logger.error(f"Loại tìm kiếm không hợp lệ hoặc thiếu embedding: {search_type}")
                return {
                    "search_results": [],
                    "error": "Loại tìm kiếm không hợp lệ hoặc thiếu embedding"
                }
            
            logger.info(f"Tìm thấy {len(results)} kết quả cho loại tìm kiếm {search_type}")
            if results:
                # Log một số kết quả đầu tiên
                for i, result in enumerate(results[:3]):
                    logger.info(f"Kết quả #{i+1}: {result.get('product_id')} - {result.get('name')} - Score: {result.get('score', 0)}")
            
            return {"search_results": results}
            
        except Exception as e:
            logger.error(f"Lỗi khi tìm kiếm: {e}")
            logger.error(f"Chi tiết lỗi: {traceback.format_exc()}")
            return {"search_results": [], "error": str(e)}
    
    def _create_filter_params(self, attributes: Dict[str, Any]) -> Optional[Filter]:
        """
        Tạo filter từ các thuộc tính.
        
        Args:
            attributes: Dict chứa các thuộc tính để lọc
            
        Returns:
            Filter object hoặc None nếu không có thuộc tính nào
        """
        if not attributes:
            return None

        conditions = []
        
        # Lọc theo brand
        if "brand" in attributes and attributes["brand"]:
            brand_value = attributes["brand"].strip()
            value_lower = brand_value.lower()

            # Ưu tiên khớp chính xác
            for brand in AVAILABLE_BRANDS:
                if brand.lower() == value_lower:
                    brand_value = brand
                    break  # Dừng luôn khi match

            else:  # Nếu không có match chính xác thì tìm match chứa
                for brand in AVAILABLE_BRANDS:
                    if value_lower in brand.lower():
                        brand_value = brand
                        break
            logger.info(f"Thêm filter brand: {brand_value}")
            conditions.append(
                FieldCondition(key="brand", match=MatchValue(value=brand_value))
            )
        else:
            return None
        # # Lọc theo gender
        # if "gender" in attributes and attributes["gender"]:
        #     gender_value = attributes["gender"]
        #     value_lower = str(gender_value).lower()
        #     gender_mapping = {
        #         "nam": "Man",
        #         "men": "Man", 
        #         "male": "Man",
        #         "nữ": "Woman", 
        #         "women": "Woman",
        #         "female": "Woman",
        #         "unisex": "Unisex"
        #     }
        #     if value_lower in gender_mapping:
        #         logger.info(f"Thêm filter gender: {gender_mapping[value_lower]}")
        #         conditions.append(
        #             FieldCondition(key="gender", match=MatchValue(value=gender_mapping[value_lower]))
        #         )
            
        # # Lọc theo category
        # if "category" in attributes and attributes["category"]:
        #     category_value = attributes["category"]
        #     logger.debug(f"Thêm filter category: {category_value}")
        #     conditions.append(
        #         FieldCondition(key="category", match=MatchValue(value=category_value))
        #     )
        
        # # Lọc theo color
        # if "color" in attributes and attributes["color"]:
        #     color_value = attributes["color"]
        #     logger.debug(f"Thêm filter color: {color_value}")
        #     conditions.append(
        #         FieldCondition(key="color", match=MatchValue(value=color_value))
        #     )
        
        # # Lọc theo frame_material
        # if "frame_material" in attributes and attributes["frame_material"]:
        #     material_value = attributes["frame_material"]
        #     logger.debug(f"Thêm filter frame_material: {material_value}")
        #     conditions.append(
        #         FieldCondition(key="frame_material", match=MatchValue(value=material_value))
        #     )
        
        # Tạo filter nếu có điều kiện
        if conditions:
            return Filter(must=conditions)
        
        return None
    
    def _search_by_text(
        self,
        text_embedding: List[float],
        limit: int,
        filter_params: Optional[Filter] = None
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm bằng text embedding.
        
        Args:
            text_embedding: Vector embedding của text
            limit: Số lượng kết quả trả về
            filter_params: Điều kiện lọc
            
        Returns:
            Danh sách kết quả tìm kiếm
        """
        # Kiểm tra filter_params trước khi gọi dict()
        if filter_params:
            logger.info(json.dumps(filter_params.dict(), indent=2))
        else:
            logger.info("Không có filter_params")
            
        search_results = self.qdrant_client.search(
            collection_name="text_products",
            query_vector=text_embedding,
            limit=limit,
            query_filter=filter_params
        )
        
        logger.info(f"Tìm thấy {len(search_results)} kết quả từ collection 'text_products'")
        return [hit.payload for hit in search_results]
    
    def _search_by_image(
        self,
        image_embedding: List[float],
        limit: int,
        filter_params: Optional[Filter] = None
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm bằng image embedding.
        
        Args:
            image_embedding: Vector embedding của image
            limit: Số lượng kết quả trả về
            filter_params: Điều kiện lọc
            
        Returns:
            Danh sách kết quả tìm kiếm
        """
        # Kiểm tra filter_params trước khi sử dụng
        if filter_params:
            logger.info(json.dumps(filter_params.dict(), indent=2))
        else:
            logger.info("Không có filter_params cho tìm kiếm image")
            
        search_results = self.qdrant_client.search(
            collection_name="image_products",
            query_vector=image_embedding,
            limit=limit,
            query_filter=filter_params
        )
        
        logger.info(f"Tìm thấy {len(search_results)} kết quả từ collection 'image_products'")
        return [hit.payload for hit in search_results]
    
    def _search_combined(
        self,
        text_embedding: List[float],
        image_embedding: List[float],
        limit: int,
        filter_params: Optional[Filter] = None,
        w_text: float = 0.6,
        w_image: float = 0.4
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm kết hợp cả text và image embedding.
        
        Args:
            text_embedding: Vector embedding của text
            image_embedding: Vector embedding của image
            limit: Số lượng kết quả trả về
            filter_params: Điều kiện lọc
            w_text: Trọng số cho điểm text
            w_image: Trọng số cho điểm image
            
        Returns:
            Danh sách kết quả tìm kiếm
        """
        from collections import defaultdict
        
        # Kiểm tra filter_params trước khi sử dụng
        if filter_params:
            logger.info(json.dumps(filter_params.dict(), indent=2))
        else:
            logger.info("Không có filter_params cho tìm kiếm combined")
        
        product_scores = defaultdict(float)
        product_details = {}
    
        # Tìm kiếm bằng text
        text_results = self.qdrant_client.search(
            collection_name="text_products",
            query_vector=text_embedding,
            limit=limit * 3,  # Tăng limit để có nhiều kết quả hơn
            query_filter=filter_params,
            with_payload=True,
            score_threshold=0.0
        )
        
        logger.info(f"Tìm thấy {len(text_results)} kết quả text từ collection 'text_products'")
        
        # Cộng điểm từ kết quả text (có trọng số)
        for hit in text_results:
            product_id = hit.payload.get("product_id")
            if product_id:
                product_scores[product_id] += hit.score * w_text
                if product_id not in product_details:
                    product_details[product_id] = hit.payload
        
        # Tìm kiếm bằng image
        logger.info(f"Tìm kiếm image trong collection 'image_products' với limit={limit*3}")
        image_results = self.qdrant_client.search(
            collection_name="image_products",
            query_vector=image_embedding,
            limit=limit * 3,
            query_filter=filter_params,
            with_payload=True,
            score_threshold=0.0
        )
        
        logger.info(f"Tìm thấy {len(image_results)} kết quả image từ collection 'image_products'")
        
        # Cộng điểm từ kết quả image (có trọng số)
        for hit in image_results:
            product_id = hit.payload.get("product_id")
            if product_id:
                product_scores[product_id] += hit.score * w_image
                if product_id not in product_details:
                    product_details[product_id] = hit.payload
        
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
        final_results = sorted_results[:limit]
        logger.info(f"Kết hợp và sắp xếp: {len(final_results)} kết quả cuối cùng")
        return final_results


# Hàm tiện ích để tạo node
def get_semantic_search_node(
    qdrant_host: str = "localhost",
    qdrant_port: int = 6333,
    default_limit: int = 5
) -> SemanticSearchNode:
    """
    Tạo một instance của SemanticSearchNode.
    
    Args:
        qdrant_host: Host của Qdrant server
        qdrant_port: Port của Qdrant server
        default_limit: Số lượng kết quả mặc định trả về
        
    Returns:
        SemanticSearchNode instance
    """
    return SemanticSearchNode(
        qdrant_host=qdrant_host,
        qdrant_port=qdrant_port,
        default_limit=default_limit
    ) 