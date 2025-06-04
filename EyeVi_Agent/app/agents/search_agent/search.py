import torch
import logging
import requests

from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

from typing import List, Dict, Optional, Union
from io import BytesIO
from collections import defaultdict


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductSearch:
    def __init__(self):
        # Khởi tạo CLIP model và processor
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        
        # Khởi tạo Qdrant client
        self.qdrant_client = QdrantClient("localhost", port=6333)
        
        # Số lượng kết quả trả về mặc định
        self.default_limit = 5

    def process_image(self, image: Union[str, Image.Image]) -> torch.Tensor:
        """Xử lý ảnh và tạo vector"""
        try:
            # Nếu image là URL
            if isinstance(image, str) and image.startswith(('http://', 'https://')):
                response = requests.get(image)
                image = Image.open(BytesIO(response.content)).convert('RGB')
            # Nếu image là đường dẫn local
            elif isinstance(image, str):
                image = Image.open(image).convert('RGB')
            
            with torch.no_grad():
                inputs = self.processor(images=image, return_tensors="pt")
                image_features = self.model.get_image_features(**inputs)
                return image_features.numpy()[0]
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return None

    def process_text(self, text: str) -> torch.Tensor:
        """Xử lý text và tạo vector"""
        try:
            print("text: ", text)
            with torch.no_grad():
                text_inputs = self.processor(text=text, return_tensors="pt", padding=True)
                text_features = self.model.get_text_features(**text_inputs)
                return text_features.numpy()[0]
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            return None

    def search_by_image(self, image: Union[str, Image.Image], 
                       limit: int = None, 
                       filter_params: Dict = None) -> List[Dict]:
        """Tìm kiếm sản phẩm bằng ảnh"""
        limit = limit or self.default_limit
        image_vector = self.process_image(image)
        
        if image_vector is None:
            return []
        
        # Tạo filter nếu có
        search_filter = None
        if filter_params:
            conditions = []
            for field, value in filter_params.items():
                conditions.append(FieldCondition(key=field, match=MatchValue(value=value)))
            search_filter = Filter(must=conditions)

        # Thực hiện tìm kiếm
        search_results = self.qdrant_client.search(
            collection_name="product_images",
            query_vector=image_vector.tolist(),
            limit=limit,
            query_filter=search_filter
        )
        
        return [hit.payload for hit in search_results]

    def search_by_text(self, text: str, 
                      limit: int = None, 
                      filter_params: Dict = None) -> List[Dict]:
        """Tìm kiếm sản phẩm bằng text"""
        limit = limit or self.default_limit
        text_vector = self.process_text(text)
        if text_vector is None:
            return []

        # Tạo filter nếu có
        search_filter = None
        if filter_params:
            conditions = []
            for field, value in filter_params.items():
                conditions.append(FieldCondition(key=field, match=MatchValue(value=value)))
            search_filter = Filter(must=conditions)
        print("search_filter: ", search_filter)
        # Thực hiện tìm kiếm
        search_results = self.qdrant_client.search(
            collection_name="product_texts",
            query_vector=text_vector.tolist(),
            limit=limit,
            query_filter=search_filter
        )
        
        return [hit.payload for hit in search_results]

    def search_combined(self, 
                       text: Optional[str] = None,
                       image: Optional[Union[str, Image.Image]] = None,
                       limit: int = None,
                       filter_params: Dict = None,
                       w_image: float = 0.4,
                       w_text: float = 0.6) -> List[Dict]:
        """
        Tìm kiếm kết hợp cả ảnh và text với trọng số
        
        Args:
            text: Câu query text
            image: Ảnh query
            limit: Số lượng kết quả trả về
            filter_params: Các điều kiện lọc
            w_image: Trọng số cho điểm ảnh (mặc định 0.6)
            w_text: Trọng số cho điểm text (mặc định 0.4)
        """
        limit = limit or self.default_limit
        product_scores = defaultdict(float)
        product_details = {}
        
        if image:
            # Lấy kết quả tìm kiếm ảnh với score
            image_results = self.qdrant_client.search(
                collection_name="product_images",
                query_vector=self.process_image(image).tolist(),
                limit=limit * 3,  # Tăng limit để có nhiều kết quả hơn cho việc kết hợp
                query_filter=None if not filter_params else Filter(
                    must=[FieldCondition(key=k, match=MatchValue(value=v)) 
                          for k, v in filter_params.items()]
                ),
                with_payload=True,
                score_threshold=0.0
            )
            
            # Cộng điểm từ kết quả ảnh (có trọng số)
            for hit in image_results:
                product_id = hit.payload["product_id"]
                product_scores[product_id] += hit.score * w_image
                if product_id not in product_details:
                    product_details[product_id] = hit.payload
        
        if text:
            # Lấy kết quả tìm kiếm text với score
            text_results = self.qdrant_client.search(
                collection_name="product_texts",
                query_vector=self.process_text(text).tolist(),
                limit=limit * 3,
                query_filter=None if not filter_params else Filter(
                    must=[FieldCondition(key=k, match=MatchValue(value=v)) 
                          for k, v in filter_params.items()]
                ),
                with_payload=True,
                score_threshold=0.0
            )
            
            # Cộng điểm từ kết quả text (có trọng số)
            for hit in text_results:
                product_id = hit.payload["product_id"]
                product_scores[product_id] += hit.score * w_text
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
        return sorted_results[:limit]

def main():
    # Ví dụ sử dụng
    search = ProductSearch()
    
    # Tìm kiếm bằng text
    text_results = search.search_by_text("kính màu trắng")
    print("Kết quả tìm kiếm bằng text:", text_results)
    
    # Tìm kiếm bằng ảnh
    image_path = "../data/test/image.png"
    image_results = search.search_by_image(image_path)
    print("Kết quả tìm kiếm bằng ảnh:", image_results)
    
    # Tìm kiếm kết hợp với trọng số
    combined_results = search.search_combined(
        text="Kính mát màu đen",
        image=image_path,
        filter_params={"brand": "Ray-Ban"},
        w_image=0.6,  # Trọng số cho ảnh
        w_text=0.4    # Trọng số cho text
    )
    print("\nKết quả tìm kiếm kết hợp:")
    for result in combined_results:
        print(f"Product ID: {result['product_id']}")
        print(f"Score: {result['score']:.4f}")
        print(f"Name: {result.get('name', 'N/A')}")
        print(f"Brand: {result.get('brand', 'N/A')}")
        print("------------------------")

if __name__ == "__main__":
    main()
