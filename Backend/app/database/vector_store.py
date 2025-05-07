from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from qdrant_client.models import Filter, FieldCondition, MatchValue
import numpy as np
from typing import List, Dict, Any, Optional, Union
from collections import defaultdict
import logging

from app.config.settings import (
    QDRANT_HOST,
    QDRANT_PORT,
    VECTOR_SIZE,
    TEXT_COLLECTION_NAME,
    IMAGE_COLLECTION_NAME
)

logger = logging.getLogger(__name__)

class VectorDatabase:
    def __init__(self):
        self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        self._create_collections_if_not_exist()
        self.default_limit = 5
    
    def _create_collections_if_not_exist(self):
        """Tạo collections nếu chưa tồn tại"""
        collections = self.client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        # Tạo collection cho text vectors nếu chưa tồn tại
        if TEXT_COLLECTION_NAME not in collection_names:
            self.client.create_collection(
                collection_name=TEXT_COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
            )
            logger.info(f"Đã tạo collection {TEXT_COLLECTION_NAME}")
        
        # Tạo collection cho image vectors nếu chưa tồn tại
        if IMAGE_COLLECTION_NAME not in collection_names:
            self.client.create_collection(
                collection_name=IMAGE_COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
            )
            logger.info(f"Đã tạo collection {IMAGE_COLLECTION_NAME}")
    
    def search_by_text_vector(self, vector: List[float], limit: int = 5, filter_params: Optional[Dict] = None) -> List[Dict]:
        """Tìm kiếm sản phẩm bằng vector text"""
        if vector is None:
            logger.warning("Vector text is None, không thể tìm kiếm")
            return []
            
        filter_obj = self._create_filter(filter_params) if filter_params else None
        
        try:
            results = self.client.search(
                collection_name=TEXT_COLLECTION_NAME,
                query_vector=vector,
                limit=limit,
                query_filter=filter_obj,
                with_payload=True,
                score_threshold=0.0
            )
            
            return self._format_results(results, collection_type="text")
        except Exception as e:
            logger.error(f"Lỗi khi tìm kiếm bằng text vector: {str(e)}")
            return []
    
    def search_by_image_vector(self, vector: List[float], limit: int = 5, filter_params: Optional[Dict] = None) -> List[Dict]:
        """Tìm kiếm sản phẩm bằng vector ảnh"""
        if vector is None:
            logger.warning("Vector ảnh is None, không thể tìm kiếm")
            return []
            
        filter_obj = self._create_filter(filter_params) if filter_params else None
        
        try:
            results = self.client.search(
                collection_name=IMAGE_COLLECTION_NAME,
                query_vector=vector,
                limit=limit,
                query_filter=filter_obj,
                with_payload=True,
                score_threshold=0.0
            )
            
            return self._format_results(results, collection_type="image")
        except Exception as e:
            logger.error(f"Lỗi khi tìm kiếm bằng image vector: {str(e)}")
            return []
    
    def search_combined(self, 
                        text_vector: Optional[List[float]] = None,
                        image_vector: Optional[List[float]] = None,
                        limit: int = 5,
                        filter_params: Optional[Dict] = None,
                        w_image: float = 0.4,
                        w_text: float = 0.6) -> List[Dict]:
        """
        Tìm kiếm kết hợp cả text vector và image vector với trọng số
        
        Args:
            text_vector: Vector text query
            image_vector: Vector ảnh query
            limit: Số lượng kết quả trả về
            filter_params: Các tham số lọc
            w_image: Trọng số cho điểm ảnh (mặc định 0.4)
            w_text: Trọng số cho điểm text (mặc định 0.6)
        """
        limit = limit or self.default_limit
        filter_obj = self._create_filter(filter_params) if filter_params else None
        
        if text_vector is None and image_vector is None:
            logger.warning("Cả text vector và image vector đều None, không thể tìm kiếm")
            return []
        
        product_scores = defaultdict(float)
        product_details = {}
        
        # Tìm kiếm bằng image vector nếu có
        if image_vector is not None:
            try:
                image_results = self.client.search(
                    collection_name=IMAGE_COLLECTION_NAME,
                    query_vector=image_vector,
                    limit=limit * 3,  # Tăng limit để có nhiều kết quả hơn cho việc kết hợp
                    query_filter=filter_obj,
                    with_payload=True,
                    score_threshold=0.0
                )
                
                # Cộng điểm từ kết quả ảnh (có trọng số)
                for hit in image_results:
                    product_id = hit.payload.get("product_id")
                    if product_id:
                        product_scores[product_id] += hit.score * w_image
                        if product_id not in product_details:
                            product_details[product_id] = {
                                "id": hit.id,
                                "payload": hit.payload,
                                "source": "image"
                            }
            except Exception as e:
                logger.error(f"Lỗi khi tìm kiếm bằng image vector: {str(e)}")
        
        # Tìm kiếm bằng text vector nếu có
        if text_vector is not None:
            try:
                text_results = self.client.search(
                    collection_name=TEXT_COLLECTION_NAME,
                    query_vector=text_vector,
                    limit=limit * 3,
                    query_filter=filter_obj,
                    with_payload=True,
                    score_threshold=0.0
                )
                
                # Cộng điểm từ kết quả text (có trọng số)
                for hit in text_results:
                    product_id = hit.payload.get("product_id")
                    if product_id:
                        product_scores[product_id] += hit.score * w_text
                        if product_id not in product_details or product_details[product_id]["source"] == "image":
                            product_details[product_id] = {
                                "id": hit.id,
                                "payload": hit.payload,
                                "source": "text"
                            }
            except Exception as e:
                logger.error(f"Lỗi khi tìm kiếm bằng text vector: {str(e)}")
        
        # Sắp xếp kết quả theo tổng điểm
        sorted_results = sorted(
            [
                {
                    "id": product_details[product_id]["id"],
                    "score": score,
                    "payload": product_details[product_id]["payload"],
                    "product_id": product_id,
                    "source": product_details[product_id]["source"]
                }
                for product_id, score in product_scores.items()
            ],
            key=lambda x: x["score"],
            reverse=True
        )
        
        # Trả về top k kết quả
        return sorted_results[:limit]
    
    def _create_filter(self, filter_params: Dict) -> Filter:
        """Tạo filter cho truy vấn"""
        conditions = []
        
        for field, value in filter_params.items():
            conditions.append(FieldCondition(key=field, match=MatchValue(value=value)))
        
        return Filter(must=conditions)
    
    def _format_results(self, results: List, collection_type: str = None) -> List[Dict]:
        """Định dạng kết quả trả về"""
        formatted_results = []
        
        for res in results:
            payload = res.payload
            # Đảm bảo rằng product_id luôn có trong kết quả
            product_id = payload.get("product_id", res.id)
            
            result = {
                "id": res.id,
                "score": res.score,
                "payload": payload,
                "product_id": product_id
            }
            
            # Thêm thông tin về nguồn dữ liệu nếu được chỉ định
            if collection_type:
                result["source"] = collection_type
            
            formatted_results.append(result)
        
        return formatted_results 